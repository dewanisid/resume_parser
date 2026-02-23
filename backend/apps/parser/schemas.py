"""
Pydantic v2 schemas for the resume parsing output.

These schemas serve two purposes:
1. Validate and normalise the JSON dict returned by the LLM
2. Provide the canonical Python structure that gets stored in
   ParsedResumeData.validated_data
"""
import re
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Leaf schemas — one per section of a resume
# ---------------------------------------------------------------------------

class Contact(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    location: Optional[str] = Field(None, max_length=150)
    # LinkedIn/GitHub kept as plain strings — LLMs often return partial URLs
    # like "linkedin.com/in/johndoe" which would fail strict HttpUrl validation
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

    @field_validator("phone", mode="before")
    @classmethod
    def normalise_phone(cls, v):
        """Strip spaces, dashes, parentheses from phone numbers."""
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-\(\)]", "", str(v))
        return cleaned if cleaned else None


class Experience(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    # YYYY-MM format, or "Present" for current roles
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def normalise_date(cls, v):
        """
        Normalise dates to YYYY-MM.
        - "Present" / "Current" / "Now"  →  "Present"
        - "2020"                          →  "2020-01"
        - "2020-06"                       →  "2020-06"  (unchanged)
        - Any other format                →  returned as-is (e.g. "Jan 2020")
        """
        if v is None:
            return v
        v = str(v).strip()
        if v.lower() in ("present", "current", "now"):
            return "Present"
        if re.match(r"^\d{4}$", v):
            return f"{v}-01"
        if re.match(r"^\d{4}-\d{2}$", v):
            return v
        return v


class Education(BaseModel):
    institution: str = Field(..., min_length=1, max_length=200)
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    location: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def normalise_date(cls, v):
        if v is None:
            return v
        v = str(v).strip()
        if re.match(r"^\d{4}$", v):
            return f"{v}-01"
        return v


class Skills(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class Language(BaseModel):
    language: str
    proficiency: Optional[str] = None


# ---------------------------------------------------------------------------
# Root schema — the full parsed resume
# ---------------------------------------------------------------------------

class ParsedResume(BaseModel):
    contact: Contact
    summary: Optional[str] = Field(None, max_length=1000)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)

    @model_validator(mode="after")
    def sort_experience_by_date(self):
        """Keep most recent job at the top of the experience list."""
        self.experience = sorted(
            self.experience,
            key=lambda x: x.start_date or "0000-00",
            reverse=True,
        )
        return self

    model_config = {"str_strip_whitespace": True}


# ---------------------------------------------------------------------------
# Confidence scoring — how complete is the extracted data?
# ---------------------------------------------------------------------------

def calculate_confidence(resume: ParsedResume) -> float:
    """
    Returns a 0.0–1.0 completeness score.

    Weights:
        Contact core fields (email, phone, location)  → 30%
        Has at least one experience entry             → 25%
        Has at least one education entry              → 20%
        Has at least one non-empty skills category    → 15%
        Has a summary                                 → 10%
    """
    score = 0.0

    # Contact completeness (up to 30%)
    contact_fields = [resume.contact.email, resume.contact.phone, resume.contact.location]
    filled = sum(1 for f in contact_fields if f)
    score += (filled / len(contact_fields)) * 0.30

    if resume.experience:
        score += 0.25

    if resume.education:
        score += 0.20

    if resume.skills.technical or resume.skills.soft or resume.skills.tools:
        score += 0.15

    if resume.summary:
        score += 0.10

    return round(score, 2)
