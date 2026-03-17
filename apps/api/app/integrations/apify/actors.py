"""
Known Apify actor IDs and their default input schemas.
"""
from __future__ import annotations

from typing import Any, Dict

# ── Actor registry ─────────────────────────────────────────────────────────────
# Format: actor_slug → {actor_id, default_input}

ACTOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "linkedin_jobs": {
        "actor_id": "curious_coder/linkedin-jobs-scraper",
        "default_input": {
            "queries": [],
            "location": "",
            "maxJobs": 100,
            "experience": [],
            "jobType": [],
            "remote": False,
        },
    },
    "indeed_jobs": {
        "actor_id": "misceres/indeed-scraper",
        "default_input": {
            "query": "",
            "location": "",
            "maxItems": 100,
            "remote": False,
        },
    },
    "glassdoor_jobs": {
        "actor_id": "bebity/glassdoor-jobs-scraper",
        "default_input": {
            "keyword": "",
            "location": "",
            "maxItems": 100,
        },
    },
    "greenhouse_jobs": {
        "actor_id": "misceres/greenhouse-jobs-scraper",
        "default_input": {
            "startUrls": [],
            "maxItems": 200,
        },
    },
    "lever_jobs": {
        "actor_id": "misceres/lever-jobs-scraper",
        "default_input": {
            "startUrls": [],
            "maxItems": 200,
        },
    },
    "wellfound_jobs": {
        "actor_id": "curious_coder/wellfound-jobs-scraper",
        "default_input": {
            "query": "",
            "location": "",
            "maxJobs": 100,
        },
    },
}


def get_actor_config(slug: str) -> Dict[str, Any]:
    """Return actor ID and default input for a known actor slug."""
    if slug not in ACTOR_REGISTRY:
        raise ValueError(f"Unknown actor slug: {slug!r}. Available: {list(ACTOR_REGISTRY)}")
    return ACTOR_REGISTRY[slug].copy()


def build_actor_input(slug: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Merge default input with user-provided overrides."""
    config = get_actor_config(slug)
    default = config["default_input"].copy()
    default.update(overrides)
    return default
