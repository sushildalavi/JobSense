"""
Normalize Apify actor output to the unified Job schema.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional


def normalize_apify_job(
    raw: Dict[str, Any],
    source_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Map a raw Apify job record to a dict suitable for constructing a Job ORM model.

    Returns None if the record is missing required fields.
    """
    # Extract title
    title = (
        raw.get("title")
        or raw.get("jobTitle")
        or raw.get("position")
        or raw.get("name")
        or ""
    ).strip()
    if not title:
        return None

    # Extract company
    company = (
        raw.get("companyName")
        or raw.get("company")
        or raw.get("employer")
        or raw.get("organization")
        or ""
    ).strip()
    if not company:
        return None

    # Source job ID — use provided ID or hash title+company+location
    source_job_id = (
        str(raw.get("id") or raw.get("jobId") or raw.get("postingId") or "")
    )
    if not source_job_id:
        fingerprint = f"{title}|{company}|{raw.get('location', '')}"
        source_job_id = hashlib.md5(fingerprint.encode()).hexdigest()

    # Location & remote
    location = str(raw.get("location") or raw.get("jobLocation") or "").strip() or None
    location_lower = (location or "").lower()
    is_remote = bool(
        raw.get("isRemote")
        or raw.get("remote")
        or "remote" in location_lower
        or "anywhere" in location_lower
    )
    is_hybrid = bool(raw.get("isHybrid") or "hybrid" in location_lower)
    is_onsite = not is_remote and not is_hybrid

    # Salary
    salary_text = str(raw.get("salary") or raw.get("salaryRange") or "").strip() or None
    salary_min, salary_max, currency = _parse_salary(salary_text or "")

    # Description
    raw_description = str(
        raw.get("description")
        or raw.get("jobDescription")
        or raw.get("descriptionHtml")
        or ""
    ).strip() or None
    cleaned_description = _clean_html(raw_description) if raw_description else None

    # URL
    apply_url = (
        raw.get("url")
        or raw.get("applyUrl")
        or raw.get("jobUrl")
        or raw.get("link")
        or None
    )

    # Posting date
    posting_date = _parse_date(
        raw.get("postedAt")
        or raw.get("datePosted")
        or raw.get("publishedAt")
        or raw.get("createdAt")
    )

    # Requirements & responsibilities
    requirements = _extract_list(raw.get("requirements") or raw.get("qualifications"))
    responsibilities = _extract_list(raw.get("responsibilities") or raw.get("duties"))

    # Employment type
    employment_type = _normalize_employment_type(
        raw.get("employmentType") or raw.get("jobType") or ""
    )

    # Seniority
    seniority = _normalize_seniority(
        raw.get("seniority") or raw.get("seniorityLevel") or title
    )

    return {
        "source_job_id": source_job_id,
        "company_name": company,
        "company_website": raw.get("companyUrl") or raw.get("companyWebsite"),
        "title": title,
        "location": location,
        "is_remote": is_remote,
        "is_hybrid": is_hybrid,
        "is_onsite": is_onsite,
        "employment_type": employment_type,
        "seniority": seniority,
        "salary_text": salary_text,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "raw_description": raw_description,
        "cleaned_description": cleaned_description,
        "requirements": requirements,
        "responsibilities": responsibilities,
        "apply_url": str(apply_url) if apply_url else None,
        "posting_date": posting_date,
    }


def _clean_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"&[a-z]+;", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _parse_salary(text: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
    """Parse salary range from text like '$120k - $160k' or '$120,000/yr'."""
    if not text:
        return None, None, None

    currency = "USD"
    if "£" in text:
        currency = "GBP"
    elif "€" in text:
        currency = "EUR"

    # Find all numbers
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", text.replace(",", ""))
    values = []
    for n in numbers:
        try:
            v = float(n.replace(",", ""))
            # Handle "k" suffix
            if "k" in text[text.find(n) + len(n):text.find(n) + len(n) + 2].lower():
                v *= 1000
            elif v < 1000:  # likely hourly — convert to annual
                v *= 2080
            values.append(int(v))
        except ValueError:
            continue

    if not values:
        return None, None, currency
    if len(values) == 1:
        return values[0], None, currency
    return min(values), max(values), currency


def _parse_date(raw: Any) -> Optional[datetime]:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        from dateutil import parser as date_parser
        return date_parser.parse(str(raw))
    except Exception:
        return None


def _extract_list(raw: Any) -> list:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if item]
    if isinstance(raw, str):
        # Split on newlines or bullets
        items = re.split(r"[\n•\-\*]", raw)
        return [item.strip() for item in items if item.strip()]
    return []


def _normalize_employment_type(raw: str) -> Optional[str]:
    raw_lower = raw.lower()
    if "full" in raw_lower:
        return "full_time"
    if "part" in raw_lower:
        return "part_time"
    if "contract" in raw_lower or "freelance" in raw_lower:
        return "contract"
    if "intern" in raw_lower:
        return "internship"
    return None


def _normalize_seniority(raw: str) -> Optional[str]:
    raw_lower = raw.lower()
    if "intern" in raw_lower:
        return "intern"
    if "junior" in raw_lower or "jr" in raw_lower or "entry" in raw_lower:
        return "junior"
    if "staff" in raw_lower:
        return "staff"
    if "principal" in raw_lower or "architect" in raw_lower:
        return "principal"
    if "director" in raw_lower:
        return "director"
    if "vp" in raw_lower or "vice president" in raw_lower:
        return "vp"
    if "cto" in raw_lower or "ceo" in raw_lower or "chief" in raw_lower:
        return "c_level"
    if "senior" in raw_lower or "sr" in raw_lower or "lead" in raw_lower:
        return "senior"
    if "mid" in raw_lower or "ii" in raw_lower or "2" in raw_lower:
        return "mid"
    return None
