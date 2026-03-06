/**
 * ResultPage — displays the full structured resume data.
 *
 * ROUTE: /results/:dataId
 *
 * useParams() reads the :dataId from the URL.
 * On mount, we fetch the parsed data from the API and display each section.
 *
 * DATA STRUCTURE REMINDER:
 * The API response shape is:
 *   { id, job_id, validated_data: { contact, summary, experience, ... }, confidence_score, ... }
 *
 * The actual resume content lives inside validated_data — not at the top level.
 *
 * OPTIONAL SECTIONS:
 * Many fields (summary, experience, education, etc.) may be null or empty arrays
 * if the resume didn't contain them. We guard every section:
 *   {experience?.length > 0 && <Card>...</Card>}
 * The ?. is "optional chaining" — it safely returns undefined instead of
 * throwing an error if experience is null.
 */

import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { resumeApi } from '../api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

// Confidence score: 0.0–1.0 float → badge with colour based on quality
function ConfidenceBadge({ score }) {
  if (score == null) return null
  const pct = Math.round(score * 100)
  const variant = pct >= 80 ? 'default' : pct >= 60 ? 'secondary' : 'destructive'
  return <Badge variant={variant}>{pct}% confidence</Badge>
}

export default function ResultPage() {
  const { dataId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    resumeApi.getData(dataId)
      .then(setData)
      .catch(() => setError('Could not load resume data.'))
      .finally(() => setLoading(false))
  }, [dataId])

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <p className="text-destructive">{error || 'No data found.'}</p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/dashboard">Back to Dashboard</Link>
        </Button>
      </div>
    )
  }

  // Destructure the nested validated_data
  const {
    contact,
    summary,
    experience,
    education,
    skills,
    certifications,
    projects,
    languages,
  } = data.validated_data

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{contact?.name || 'Resume'}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ConfidenceBadge score={data.confidence_score} />
            <span className="text-xs text-muted-foreground">
              via {data.extraction_method} · {data.llm_model}
            </span>
          </div>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/dashboard">← Back</Link>
        </Button>
      </div>

      <Separator />

      {/* Contact */}
      {contact && (
        <Card>
          <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm">
            {contact.email && <p>📧 {contact.email}</p>}
            {contact.phone && <p>📞 {contact.phone}</p>}
            {contact.location && <p>📍 {contact.location}</p>}
            {contact.linkedin && (
              <p>
                🔗{' '}
                <a href={contact.linkedin} target="_blank" rel="noreferrer"
                   className="text-primary underline">
                  LinkedIn
                </a>
              </p>
            )}
            {contact.github && (
              <p>
                🐙{' '}
                <a href={contact.github} target="_blank" rel="noreferrer"
                   className="text-primary underline">
                  GitHub
                </a>
              </p>
            )}
            {contact.portfolio && (
              <p>
                🌐{' '}
                <a href={contact.portfolio} target="_blank" rel="noreferrer"
                   className="text-primary underline">
                  Portfolio
                </a>
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      {summary && (
        <Card>
          <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Experience */}
      {experience?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Experience</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            {experience.map((exp, i) => (
              <div key={i} className={i > 0 ? 'pt-5 border-t' : ''}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{exp.company}</p>
                    <p className="text-sm text-muted-foreground">{exp.title}</p>
                  </div>
                  <p className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                    {exp.start_date} – {exp.end_date || 'Present'}
                  </p>
                </div>
                {exp.location && (
                  <p className="text-xs text-muted-foreground mt-0.5">{exp.location}</p>
                )}
                {exp.description && (
                  <p className="mt-2 text-sm">{exp.description}</p>
                )}
                {exp.achievements?.length > 0 && (
                  <ul className="mt-2 space-y-1 list-disc list-inside text-sm">
                    {exp.achievements.map((a, j) => <li key={j}>{a}</li>)}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Education */}
      {education?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Education</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {education.map((edu, i) => (
              <div key={i} className={i > 0 ? 'pt-4 border-t' : ''}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{edu.institution}</p>
                    <p className="text-sm text-muted-foreground">
                      {[edu.degree, edu.field_of_study].filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                    {edu.start_date} – {edu.end_date || 'Present'}
                  </p>
                </div>
                {edu.gpa && (
                  <p className="text-xs text-muted-foreground mt-0.5">GPA: {edu.gpa}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Skills */}
      {skills && (skills.technical?.length > 0 || skills.soft?.length > 0 || skills.tools?.length > 0) && (
        <Card>
          <CardHeader><CardTitle>Skills</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {skills.technical?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
                  Technical
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {skills.technical.map((s) => (
                    <Badge key={s} variant="secondary">{s}</Badge>
                  ))}
                </div>
              </div>
            )}
            {skills.tools?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
                  Tools
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {skills.tools.map((s) => (
                    <Badge key={s} variant="outline">{s}</Badge>
                  ))}
                </div>
              </div>
            )}
            {skills.soft?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
                  Soft Skills
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {skills.soft.map((s) => (
                    <Badge key={s} variant="outline">{s}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Certifications */}
      {certifications?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Certifications</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {certifications.map((cert, i) => (
              <div key={i} className="text-sm">
                <span className="font-medium">{cert.name}</span>
                {cert.issuer && <span className="text-muted-foreground"> · {cert.issuer}</span>}
                {cert.date && <span className="text-muted-foreground"> · {cert.date}</span>}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Projects */}
      {projects?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Projects</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {projects.map((proj, i) => (
              <div key={i} className={i > 0 ? 'pt-4 border-t' : ''}>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-sm">{proj.name}</p>
                  {proj.url && (
                    <a href={proj.url} target="_blank" rel="noreferrer"
                       className="text-xs text-primary underline">
                      Link
                    </a>
                  )}
                </div>
                {proj.description && (
                  <p className="text-sm mt-1">{proj.description}</p>
                )}
                {proj.technologies?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {proj.technologies.map((t) => (
                      <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Languages */}
      {languages?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Languages</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {languages.map((lang, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span className="text-sm">{lang.language}</span>
                  {lang.proficiency && (
                    <Badge variant="secondary" className="text-xs">{lang.proficiency}</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

    </main>
  )
}
