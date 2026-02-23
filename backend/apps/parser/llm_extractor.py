"""
LLMExtractor — sends resume text to Anthropic Claude and returns
structured JSON matching the ParsedResume schema.

Key behaviours:
- Uses claude-haiku-4-5-20251001 by default (fast and cheap)
- Low temperature (0.1) for consistent, deterministic extraction
- Exponential backoff retry on API errors (up to MAX_RETRIES attempts)
- Strips known prompt-injection patterns from resume text before sending
- Returns (raw_dict, usage_meta) tuple for storage in ParsedResumeData
"""
import json
import logging
import re
import time
from typing import Any, Dict, Tuple

import anthropic
from django.conf import settings

logger = logging.getLogger("apps.parser")

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert resume parser. Extract structured information
from the resume text and return it as a single valid JSON object.

Rules:
- Use null for any field that is missing or unclear. NEVER invent or guess data.
- Preserve the candidate's original wording for descriptions and achievements.
- Normalise dates to YYYY-MM format. Use "Present" for current/ongoing roles.
- Standardise location to "City, Country" where possible.
- Return ONLY the JSON object. No markdown fences, no explanation, no extra text."""

# Double curly braces {{ }} are needed because Python's .format() uses single braces
USER_PROMPT_TEMPLATE = """Extract all information from the resume below and return
a JSON object with exactly this structure:

{{
  "contact": {{
    "name": "Full name",
    "email": "email@example.com or null",
    "phone": "+1234567890 or null",
    "location": "City, Country or null",
    "linkedin": "URL or null",
    "github": "URL or null",
    "portfolio": "URL or null"
  }},
  "summary": "2-3 sentence professional summary, or null",
  "experience": [
    {{
      "company": "Company name",
      "title": "Job title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "location": "City, Country or null",
      "description": "Role description or null",
      "achievements": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "education": [
    {{
      "institution": "University name",
      "degree": "B.S. / M.S. / PhD / etc.",
      "field": "Field of study",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "gpa": "3.8/4.0 or null",
      "location": "City, Country or null"
    }}
  ],
  "skills": {{
    "technical": ["Python", "SQL", "React"],
    "soft": ["Leadership", "Communication"],
    "tools": ["Git", "Docker", "AWS"]
  }},
  "certifications": [
    {{
      "name": "Certification name",
      "issuer": "Issuing organisation",
      "date": "YYYY-MM or null",
      "credential_id": "ID or null"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech1", "Tech2"],
      "url": "URL or null"
    }}
  ],
  "languages": [
    {{
      "language": "Language name",
      "proficiency": "Native / Fluent / Professional / Basic"
    }}
  ]
}}

Resume text:
---
{resume_text}
---

JSON output:"""

# ---------------------------------------------------------------------------
# Prompt injection — patterns to strip before sending to the LLM
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:", re.IGNORECASE),
    re.compile(r"<\|im_start\|>"),
    re.compile(r"<\|im_end\|>"),
    re.compile(r"\[INST\]"),
    re.compile(r"\[/INST\]"),
]


def _sanitize(text: str) -> str:
    """Remove known prompt-injection patterns from resume text."""
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("", text)
    return text


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------

class LLMExtractionError(Exception):
    pass


class LLMExtractor:

    def __init__(self):
        cfg = settings.LLM_SETTINGS
        self.model = cfg["MODEL"]
        self.max_tokens = cfg["MAX_TOKENS"]
        self.temperature = cfg["TEMPERATURE"]
        self.max_retries = cfg["MAX_RETRIES"]
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def extract_structured_data(
        self, resume_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Send resume text to Claude and get back structured JSON.

        Returns:
            (raw_dict, usage_meta)
            raw_dict   — the parsed JSON dict from the LLM response
            usage_meta — {"model", "input_tokens", "output_tokens", "cost_usd"}

        Raises:
            LLMExtractionError after all retries are exhausted.
        """
        clean_text = _sanitize(resume_text)
        user_message = USER_PROMPT_TEMPLATE.format(resume_text=clean_text)

        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("LLM call attempt %d/%d (model=%s)", attempt, self.max_retries, self.model)

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                )

                raw_text = response.content[0].text.strip()

                # Claude sometimes wraps its response in markdown code fences
                # even when told not to — strip them defensively
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text).strip()

                raw_dict = json.loads(raw_text)

                usage_meta = self._build_usage_meta(response)
                logger.info(
                    "LLM extraction succeeded — %d input + %d output tokens",
                    usage_meta["input_tokens"], usage_meta["output_tokens"],
                )
                return raw_dict, usage_meta

            except json.JSONDecodeError as exc:
                logger.warning("Invalid JSON on attempt %d: %s", attempt, exc)
                last_exception = LLMExtractionError(f"LLM returned invalid JSON: {exc}")
                # No sleep for JSON errors — retry immediately

            except anthropic.RateLimitError as exc:
                wait = 2 ** attempt
                logger.warning("Rate limit hit — waiting %ds before attempt %d", wait, attempt + 1)
                time.sleep(wait)
                last_exception = exc

            except anthropic.APIError as exc:
                wait = 2 ** attempt
                logger.warning("API error on attempt %d (%s) — retrying in %ds", attempt, exc, wait)
                time.sleep(wait)
                last_exception = exc

        raise LLMExtractionError(
            f"LLM extraction failed after {self.max_retries} attempts: {last_exception}"
        ) from last_exception

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_usage_meta(self, response) -> Dict[str, Any]:
        """Extract token counts and estimate cost from an API response."""
        usage = response.usage
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens

        # claude-haiku-4-5 pricing (as of Feb 2026):
        # Input:  $0.80 per million tokens
        # Output: $4.00 per million tokens
        cost = (input_tokens * 0.80 + output_tokens * 4.00) / 1_000_000

        return {
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 8),
        }
