"""
Versioned prompt templates for all AI workflows.
"""

from __future__ import annotations

# ── Job Matching ───────────────────────────────────────────────────────────────

JOB_MATCH_PROMPT_V1 = """You are an expert career coach and recruiter.
Analyze how well a candidate's profile matches a job posting.

# Candidate Profile
Skills: {skills}
Seniority Level: {seniority_level}
Years of Experience: {years_of_experience}
Target Roles: {target_roles}
Remote Preference: {remote_preference}

# Job Posting
Title: {job_title}
Company: {company}
Location: {location}
Seniority: {job_seniority}
Employment Type: {employment_type}
Description: {job_description}
Requirements: {requirements}

# Instructions
Provide a JSON object with these exact fields:
- match_score: float 0.0–1.0 (overall fit)
- skill_matches: list of skills the candidate has that are required
- skill_gaps: list of required skills the candidate lacks
- strengths: list of candidate strengths for this role (2–4 items)
- weaknesses: list of concerns or gaps (2–4 items)
- explanation: 2–3 sentence summary of the fit

Respond ONLY with valid JSON, no markdown fences.
"""

# ── Resume Tailoring ───────────────────────────────────────────────────────────

RESUME_TAILORING_PROMPT_V1 = """You are an expert resume writer.
Tailor the candidate's resume for a specific job posting.
DO NOT invent experience or skills. Only rephrase, reorder, and emphasize existing content.

# Job Posting
Title: {job_title}
Company: {company}
Description: {job_description}
Key Requirements: {requirements}

# Current Resume Content
{resume_text}

# Instructions
Return a JSON object with these exact fields:
- tailored_content: the complete rewritten resume text (Markdown format)
- sections_modified: list of section names that were changed
- keywords_added: list of keywords from the job description that were woven in
- reasoning: brief explanation of the main changes made

Respond ONLY with valid JSON, no markdown fences.
"""

# ── Resume Parsing ─────────────────────────────────────────────────────────────

RESUME_PARSE_PROMPT_V1 = """Extract structured data from this resume text.

Resume:
{resume_text}

Return a JSON object with these fields:
- contact: {{name, email, phone, location, linkedin_url, github_url, portfolio_url}}
- summary: string or null
- work_experience:
  list of {{company, title, start_date, end_date, is_current, location, bullets, technologies}}
- education: list of {{institution, degree, field_of_study, start_date, end_date, gpa}}
- projects: list of {{name, description, technologies, bullets, url}}
- skills: {{languages, frameworks, tools, databases, cloud, other}}
- certifications: list of {{name, issuer, date}}
- total_years_experience: float or null
- all_skills_flat: flat list of all skills mentioned

Respond ONLY with valid JSON, no markdown fences.
"""

# ── Email Classification ───────────────────────────────────────────────────────

EMAIL_CLASSIFICATION_PROMPT_V1 = """You are a recruiting email classifier.
Classify this email thread.

Email Subject: {subject}
Email Body: {body}
Sender: {sender}

Classify into exactly one of these categories:
- recruiter_outreach: initial reach-out from a recruiter
- oa_assessment: online assessment or coding challenge
- interview_scheduling: request to schedule an interview
- interview_confirmation: confirmed interview details
- rejection: application rejected
- offer: job offer extended
- follow_up: follow-up on application status
- noise: unrelated to job search

Return a JSON object:
- classification: one of the categories above
- confidence: float 0.0–1.0
- reasoning: one sentence explanation

Respond ONLY with valid JSON, no markdown fences.
"""

# ── Email Entity Extraction ────────────────────────────────────────────────────

EMAIL_ENTITY_EXTRACTION_PROMPT_V1 = """Extract structured entities from this recruiting email.

Email Content:
{email_content}

Extract and return a JSON object with these fields (use null if not found):
- company: company name
- job_title: job title being discussed
- interviewer: name of interviewer or recruiter
- interview_datetime: ISO 8601 datetime string (e.g. "2024-03-15T14:00:00")
- timezone: timezone name (e.g. "America/New_York", "PST", "UTC")
- meeting_link: video call URL (Zoom, Google Meet, Teams, etc.)
- next_action: what the candidate should do next

Respond ONLY with valid JSON, no markdown fences.
"""

# ── Follow-up Draft ────────────────────────────────────────────────────────────

FOLLOW_UP_DRAFT_PROMPT_V1 = """Draft a professional follow-up email for a job application.

Company: {company}
Job Title: {job_title}
Applied Date: {applied_date}
Interviewer/Contact: {contact_name}
Previous Interaction: {context}
Candidate Name: {candidate_name}

Write a concise, professional follow-up email. Return JSON:
- subject: email subject line
- body: email body (plain text, 3–5 sentences)
- tone: "professional" | "warm" | "brief"

Respond ONLY with valid JSON, no markdown fences.
"""
