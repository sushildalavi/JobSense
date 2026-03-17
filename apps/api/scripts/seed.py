#!/usr/bin/env python3
"""
Seed the database with realistic demo data for development and demos.

Usage:
    cd apps/api
    python scripts/seed.py

The script is idempotent: it checks for the demo user before inserting,
so running it twice will not create duplicate data.
"""

from __future__ import annotations

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure the project root is on sys.path when run directly.
sys.path.insert(0, ".")

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.agent import (
    AgentRun,
    AgentRunStatus,
    WorkflowName,
)
from app.models.application import Application, ApplicationEvent, ApplicationStatus, TriggeredBy
from app.models.calendar import CalendarEvent, CalendarEventStatus
from app.models.email import EmailClassification, EmailThread, ParsedEmail
from app.models.job import EmploymentType, Job, JobMatch, JobSeniority, JobSource, JobStatus
from app.models.profile import Profile, RemotePreference, SeniorityLevel
from app.models.resume import MasterResume, ResumeVersion
from app.models.user import User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


def days_ago(n: int) -> datetime:
    return utcnow() - timedelta(days=n)


def days_from_now(n: int) -> datetime:
    return utcnow() + timedelta(days=n)


# ---------------------------------------------------------------------------
# Demo data constants
# ---------------------------------------------------------------------------

DEMO_EMAIL = "demo@applyflow.dev"
DEMO_PASSWORD = "DemoPass123"

SKILLS = [
    "Python",
    "PyTorch",
    "TensorFlow",
    "JAX",
    "Scikit-learn",
    "SQL",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Kubernetes",
    "FastAPI",
    "LangChain",
    "LangGraph",
    "OpenAI API",
    "Anthropic API",
    "AWS SageMaker",
    "MLflow",
    "Weights & Biases",
    "Ray",
    "Spark",
    "Data pipelines",
    "Feature engineering",
    "A/B testing",
    "Distributed training",
    "RLHF",
    "RAG",
]

JOB_LISTINGS = [
    {
        "title": "Senior ML Engineer",
        "company_name": "OpenMind AI",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 200_000,
        "salary_max": 280_000,
        "currency": "USD",
        "raw_description": (
            "Build and scale LLM inference infrastructure. Partner with research to "
            "productionize cutting-edge models. Drive 10× latency improvements through "
            "quantization, distillation, and speculative decoding. 5+ years ML, strong "
            "Python, CUDA experience preferred."
        ),
        "requirements": ["Python", "PyTorch", "CUDA", "distributed training", "5+ years ML"],
        "responsibilities": ["Model serving", "Infra optimization", "Research collaboration"],
    },
    {
        "title": "AI Engineer — Agents & Tooling",
        "company_name": "Anthropic",
        "location": "San Francisco, CA",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 220_000,
        "salary_max": 350_000,
        "currency": "USD",
        "raw_description": (
            "Join the Claude product team to build agentic capabilities. Design tool-use "
            "frameworks, multi-agent orchestration, and safety guardrails. Work directly "
            "with frontier model researchers. Strong systems thinking + Python required."
        ),
        "requirements": ["Python", "LLM APIs", "systems design", "safety mindset"],
        "responsibilities": ["Agent frameworks", "Tool integration", "Safety evaluation"],
    },
    {
        "title": "Machine Learning Engineer — Ranking",
        "company_name": "Meta AI",
        "location": "Menlo Park, CA",
        "is_remote": False,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 250_000,
        "salary_max": 400_000,
        "currency": "USD",
        "raw_description": (
            "Own ranking and recommendation systems serving billions of users. "
            "Design features, run large-scale A/B tests, and deploy real-time models. "
            "PhD or 6+ years industry ML experience."
        ),
        "requirements": [
            "Python",
            "PyTorch",
            "A/B testing",
            "large-scale systems",
            "recommendation systems",
        ],
        "responsibilities": ["Feature engineering", "Model training", "Production deployment"],
    },
    {
        "title": "Research Scientist — NLP",
        "company_name": "DeepMind",
        "location": "London, UK",
        "is_remote": True,
        "seniority": JobSeniority.staff,
        "employment_type": EmploymentType.full_time,
        "salary_min": 160_000,
        "salary_max": 250_000,
        "currency": "GBP",
        "raw_description": (
            "Conduct fundamental research on language models, alignment, and reasoning. "
            "Publish at top venues (NeurIPS, ICML, ACL). Collaborate across Gemini teams. "
            "Strong ML theory + Python. PhD required."
        ),
        "requirements": ["PhD", "Python", "JAX", "research publications", "NLP"],
        "responsibilities": ["Novel research", "Paper writing", "Model evaluation"],
    },
    {
        "title": "Staff ML Engineer — Infrastructure",
        "company_name": "Stripe",
        "location": "Remote",
        "is_remote": True,
        "seniority": JobSeniority.staff,
        "employment_type": EmploymentType.full_time,
        "salary_min": 300_000,
        "salary_max": 450_000,
        "currency": "USD",
        "raw_description": (
            "Build the ML platform powering fraud detection and financial intelligence "
            "across millions of businesses. Architect feature stores, model registries, "
            "and real-time inference pipelines. 8+ years experience."
        ),
        "requirements": ["Python", "MLflow", "Kubernetes", "feature stores", "8+ years"],
        "responsibilities": ["ML platform", "Feature pipelines", "Real-time inference"],
    },
    {
        "title": "ML Engineer — Generative AI Products",
        "company_name": "Adobe",
        "location": "San Jose, CA",
        "is_remote": True,
        "is_hybrid": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 150_000,
        "salary_max": 210_000,
        "currency": "USD",
        "raw_description": (
            "Develop Firefly and Sensei AI products used by 30 million creatives. "
            "Fine-tune diffusion models, implement LoRA adapters, build evaluation pipelines. "
            "3–5 years experience with generative models."
        ),
        "requirements": ["Python", "diffusion models", "LoRA", "generative AI", "3+ years"],
        "responsibilities": ["Model fine-tuning", "Product integration", "Evaluation"],
    },
    {
        "title": "Applied AI Engineer",
        "company_name": "Cohere",
        "location": "Toronto, Canada",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 130_000,
        "salary_max": 190_000,
        "currency": "USD",
        "raw_description": (
            "Help enterprise customers deploy Cohere's language models. Build RAG pipelines, "
            "evaluation frameworks, and integration tooling. Strong Python + LangChain/LlamaIndex."
        ),
        "requirements": ["Python", "RAG", "LangChain", "API integration", "enterprise"],
        "responsibilities": ["Customer integrations", "RAG systems", "Demo pipelines"],
    },
    {
        "title": "Senior AI Research Engineer",
        "company_name": "Mistral AI",
        "location": "Paris, France",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 120_000,
        "salary_max": 200_000,
        "currency": "EUR",
        "raw_description": (
            "Work on next-generation open-weight models. Implement training recipes, "
            "design evaluation benchmarks, and contribute to research papers. "
            "Deep PyTorch + HPC cluster experience."
        ),
        "requirements": ["Python", "PyTorch", "HPC", "training optimization", "research"],
        "responsibilities": ["Training runs", "Evaluation", "Research contributions"],
    },
    {
        "title": "ML Platform Engineer",
        "company_name": "Airbnb",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 230_000,
        "salary_max": 330_000,
        "currency": "USD",
        "raw_description": (
            "Own Airbnb's ML platform — feature store, model registry, online serving. "
            "Reduce time-to-production for 100+ data scientists. Kubernetes, Spark, Ray."
        ),
        "requirements": ["Python", "Spark", "Ray", "Kubernetes", "MLflow", "platform engineering"],
        "responsibilities": ["Feature store", "Model registry", "Serving infra"],
    },
    {
        "title": "NLP Engineer",
        "company_name": "Hugging Face",
        "location": "Remote",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 140_000,
        "salary_max": 190_000,
        "currency": "USD",
        "raw_description": (
            "Build open-source NLP tools used by 5 million researchers. "
            "Contribute to Transformers, Datasets, and Hub. Strong Python + OSS mindset."
        ),
        "requirements": ["Python", "PyTorch", "Transformers", "open source", "NLP"],
        "responsibilities": ["Library development", "Model integrations", "Documentation"],
    },
    {
        "title": "ML Engineer — Search",
        "company_name": "Elastic",
        "location": "Remote",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 160_000,
        "salary_max": 220_000,
        "currency": "USD",
        "raw_description": (
            "Build vector search and semantic ranking at Elasticsearch scale. "
            "Integrate dense embeddings, sparse models, and hybrid retrieval. Python + Java."
        ),
        "requirements": ["Python", "vector search", "embeddings", "information retrieval"],
        "responsibilities": ["Embedding integration", "Ranking models", "Search quality"],
    },
    {
        "title": "AI/ML Software Engineer",
        "company_name": "Apple",
        "location": "Cupertino, CA",
        "is_remote": False,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 250_000,
        "salary_max": 400_000,
        "currency": "USD",
        "raw_description": (
            "Join Apple Intelligence teams building on-device AI. Design efficient "
            "model architectures for iOS/macOS, implement CoreML pipelines, balance "
            "performance with privacy. C++ and Python required."
        ),
        "requirements": ["Python", "C++", "CoreML", "on-device AI", "privacy engineering"],
        "responsibilities": ["On-device models", "CoreML pipelines", "Performance optimization"],
    },
    {
        "title": "Senior Data Scientist — ML",
        "company_name": "Spotify",
        "location": "New York, NY",
        "is_remote": True,
        "is_hybrid": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 180_000,
        "salary_max": 260_000,
        "currency": "USD",
        "raw_description": (
            "Power music recommendations for 600M listeners. Build causal models, "
            "design experiments, collaborate with engineering to ship at scale. "
            "Python + Spark + strong statistics."
        ),
        "requirements": [
            "Python",
            "Spark",
            "statistics",
            "causal inference",
            "recommendation systems",
        ],
        "responsibilities": ["Recommendation models", "Experimentation", "Causal analysis"],
    },
    {
        "title": "Founding AI Engineer",
        "company_name": "Stealth AI Startup",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 170_000,
        "salary_max": 230_000,
        "currency": "USD",
        "raw_description": (
            "First AI hire at a well-funded stealth company disrupting enterprise workflows. "
            "Build agent systems end-to-end: prompt engineering, RAG, evals, and product. "
            "Equity upside. Velocity-first culture."
        ),
        "requirements": ["Python", "LangGraph", "RAG", "OpenAI", "Anthropic", "startup mindset"],
        "responsibilities": ["Agent development", "Product engineering", "Evals"],
    },
    {
        "title": "ML Research Engineer — Vision",
        "company_name": "Scale AI",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 170_000,
        "salary_max": 240_000,
        "currency": "USD",
        "raw_description": (
            "Build the data and model infrastructure for the world's leading AI data "
            "labeling company. Work on multimodal models, active learning, and quality "
            "estimation. 3+ years ML + Python."
        ),
        "requirements": ["Python", "PyTorch", "computer vision", "active learning", "multimodal"],
        "responsibilities": ["Data labeling models", "Quality estimation", "Multimodal research"],
    },
    {
        "title": "Principal ML Engineer",
        "company_name": "Waymo",
        "location": "Mountain View, CA",
        "is_remote": False,
        "seniority": JobSeniority.principal,
        "employment_type": EmploymentType.full_time,
        "salary_min": 350_000,
        "salary_max": 550_000,
        "currency": "USD",
        "raw_description": (
            "Lead ML strategy for Waymo's perception team. Design large-scale 3D "
            "object detection architectures, mentor senior engineers, define technical "
            "roadmap. 10+ years, strong publications background."
        ),
        "requirements": ["Python", "C++", "3D perception", "deep learning", "10+ years"],
        "responsibilities": ["Technical leadership", "Architecture design", "Mentorship"],
    },
    {
        "title": "ML Engineer — Conversational AI",
        "company_name": "Amazon Alexa",
        "location": "Seattle, WA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 200_000,
        "salary_max": 300_000,
        "currency": "USD",
        "raw_description": (
            "Advance Alexa's dialogue systems with LLM-based response generation, "
            "entity resolution, and contextual understanding. Millions of daily users. "
            "Python + AWS infrastructure."
        ),
        "requirements": ["Python", "AWS", "NLU", "dialogue systems", "LLMs"],
        "responsibilities": ["Dialogue modeling", "Entity extraction", "LLM integration"],
    },
    {
        "title": "AI Infrastructure Engineer",
        "company_name": "Together AI",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 180_000,
        "salary_max": 260_000,
        "currency": "USD",
        "raw_description": (
            "Build the cloud infrastructure serving open-source LLMs at scale. "
            "Design distributed inference pipelines, optimize GPU utilization, "
            "maintain 99.9% uptime SLAs. Kubernetes + CUDA + Python."
        ),
        "requirements": ["Python", "Kubernetes", "CUDA", "distributed systems", "GPU"],
        "responsibilities": ["GPU cluster management", "Inference optimization", "SLA maintenance"],
    },
    {
        "title": "Senior MLOps Engineer",
        "company_name": "Databricks",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 220_000,
        "salary_max": 320_000,
        "currency": "USD",
        "raw_description": (
            "Build MLflow and Mosaic platform features used by 10,000+ data science teams. "
            "Design experiment tracking, model registry, and CI/CD for ML. "
            "Python + Spark + open source."
        ),
        "requirements": ["Python", "Spark", "MLflow", "open source", "MLOps"],
        "responsibilities": ["Platform features", "OSS contributions", "Customer success"],
    },
    {
        "title": "Deep Learning Engineer — LLM Fine-tuning",
        "company_name": "Perplexity AI",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 210_000,
        "salary_max": 300_000,
        "currency": "USD",
        "raw_description": (
            "Fine-tune and align LLMs for Perplexity's answer engine. "
            "Run RLHF/DPO pipelines, evaluate models for factual accuracy, "
            "and ship fast. Strong Python + PyTorch + distributed training."
        ),
        "requirements": ["Python", "PyTorch", "RLHF", "DPO", "distributed training", "alignment"],
        "responsibilities": ["Fine-tuning pipelines", "RLHF/DPO", "Factuality evaluation"],
    },
    {
        "title": "ML Intern — Summer 2026",
        "company_name": "Google DeepMind",
        "location": "New York, NY",
        "is_remote": False,
        "seniority": JobSeniority.intern,
        "employment_type": EmploymentType.internship,
        "salary_min": 8_000,
        "salary_max": 12_000,
        "currency": "USD",
        "raw_description": (
            "12-week research internship on safety, reasoning, or perception. "
            "Work alongside research scientists on publishable projects. "
            "Currently enrolled in PhD/MS program, Python + ML fundamentals."
        ),
        "requirements": ["Python", "ML fundamentals", "PhD/MS enrollment", "research interest"],
        "responsibilities": ["Research project", "Paper contribution", "Presentations"],
    },
    {
        "title": "Contract ML Engineer (6-month)",
        "company_name": "Snowflake",
        "location": "Remote",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.contract,
        "salary_min": 180_000,
        "salary_max": 200_000,
        "currency": "USD",
        "raw_description": (
            "Six-month contract to build Cortex ML features in Snowpark. "
            "Deliver time-series forecasting and anomaly detection models. "
            "Python + Spark + SQL."
        ),
        "requirements": ["Python", "Spark", "SQL", "time series", "anomaly detection"],
        "responsibilities": ["Feature development", "Model delivery", "Documentation"],
    },
    {
        "title": "AI Product Engineer",
        "company_name": "Notion",
        "location": "San Francisco, CA",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 160_000,
        "salary_max": 230_000,
        "currency": "USD",
        "raw_description": (
            "Build AI features across Notion: Q&A over workspaces, smart suggestions, "
            "and autofill. Work at the intersection of product and ML. "
            "React + Python + LLM APIs."
        ),
        "requirements": ["Python", "React", "LLM APIs", "product thinking", "RAG"],
        "responsibilities": ["AI features", "Prompt engineering", "User research"],
    },
    {
        "title": "Machine Learning Engineer — Trust & Safety",
        "company_name": "Roblox",
        "location": "San Mateo, CA",
        "is_remote": True,
        "seniority": JobSeniority.mid,
        "employment_type": EmploymentType.full_time,
        "salary_min": 165_000,
        "salary_max": 225_000,
        "currency": "USD",
        "raw_description": (
            "Protect 70 million daily users with ML-powered content moderation, "
            "account security, and fraud detection. Real-time classifiers at scale. "
            "Python + AWS + strong ethics."
        ),
        "requirements": ["Python", "AWS", "classifiers", "fraud detection", "content moderation"],
        "responsibilities": ["Classifier development", "Safety evaluation", "Policy collaboration"],
    },
    {
        "title": "Research Engineer — Multimodal Models",
        "company_name": "Stability AI",
        "location": "Remote",
        "is_remote": True,
        "seniority": JobSeniority.senior,
        "employment_type": EmploymentType.full_time,
        "salary_min": 140_000,
        "salary_max": 210_000,
        "currency": "USD",
        "raw_description": (
            "Advance open-source multimodal models: image, video, audio generation. "
            "Implement training improvements, run large-scale experiments, "
            "contribute to open-source releases. Python + JAX/PyTorch."
        ),
        "requirements": [
            "Python",
            "JAX",
            "PyTorch",
            "diffusion models",
            "multimodal",
            "open source",
        ],
        "responsibilities": ["Model training", "Research experiments", "OSS releases"],
    },
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


async def seed(session: AsyncSession) -> None:
    print("🌱  Starting seed...")

    # ── Check idempotency ────────────────────────────────────────────────────
    result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        print(f"   Demo user already exists ({DEMO_EMAIL}). Skipping seed.")
        return

    # ── User ────────────────────────────────────────────────────────────────
    print("   Creating demo user...")
    user = User(
        email=DEMO_EMAIL,
        hashed_password=pwd_ctx.hash(DEMO_PASSWORD),
        full_name="Alex Chen",
        is_active=True,
        is_verified=True,
        last_login_at=days_ago(1),
    )
    session.add(user)
    await session.flush()

    # ── Profile ─────────────────────────────────────────────────────────────
    print("   Creating profile...")
    profile = Profile(
        user_id=user.id,
        target_roles=[
            "ML Engineer",
            "Senior ML Engineer",
            "AI Engineer",
            "Research Engineer",
            "Staff ML Engineer",
        ],
        preferred_locations=["San Francisco, CA", "Remote", "New York, NY"],
        remote_preference=RemotePreference.remote,
        seniority_level=SeniorityLevel.senior,
        preferred_industries=["AI/ML", "Big Tech", "Fintech", "Startups"],
        years_of_experience=6,
        visa_status="US Citizen",
        work_authorization="Authorized to work in US",
        preferred_salary_min=180_000,
        preferred_salary_max=350_000,
        preferred_currency="USD",
        skills=SKILLS,
        keywords_to_prioritize=["LLM", "GenAI", "agents", "PyTorch", "RAG"],
        keywords_to_avoid=["COBOL", "mainframe", "PHP"],
        linkedin_url="https://linkedin.com/in/alex-chen-ml",
        github_url="https://github.com/alex-chen-ml",
        portfolio_url="https://alexchen.ai",
    )
    session.add(profile)
    await session.flush()

    # ── Master Resume ────────────────────────────────────────────────────────
    print("   Creating master resume...")
    master_resume = MasterResume(
        user_id=user.id,
        name="Alex Chen — Master Resume 2026",
        raw_text=(
            "ALEX CHEN\nSenior ML Engineer\nalex@applyflow.dev | linkedin.com/in/alex-chen-ml\n\n"
            "EXPERIENCE\n\n"
            "Senior ML Engineer — Acme AI (2022–Present)\n"
            "• Built real-time recommendation system serving 50M daily requests at p99 < 10ms\n"
            "• Led migration of training pipelines to distributed PyTorch (8× speedup)\n"
            "• Reduced model serving costs 40% via quantization and speculative decoding\n\n"
            "ML Engineer — TechCorp (2020–2022)\n"
            "• Developed NLP pipeline for automated document classification (95% accuracy)\n"
            "• Deployed LLM-based search improving CTR by 23%\n\n"
            "EDUCATION\nMS Computer Science (ML focus) — Stanford University, 2020\n"
            "BS Computer Science — UC Berkeley, 2018\n\n"
            "SKILLS\nPython · PyTorch · TensorFlow · LangGraph · FastAPI · PostgreSQL · Redis "
            "· Docker · Kubernetes · AWS · SQL · Spark · MLflow · W&B"
        ),
        parsed_data={
            "name": "Alex Chen",
            "contact": {"email": "alex@applyflow.dev"},
            "education": [
                {"degree": "MS CS", "school": "Stanford University", "year": 2020},
                {"degree": "BS CS", "school": "UC Berkeley", "year": 2018},
            ],
            "experience_years": 6,
            "skills": SKILLS[:20],
        },
        is_active=True,
    )
    session.add(master_resume)
    await session.flush()

    # ── Job Sources ──────────────────────────────────────────────────────────
    print("   Creating job sources...")
    sources = [
        JobSource(
            name="Apify LinkedIn Scraper",
            connector_type="apify_linkedin",
            config={"actor_id": "curious_coder/linkedin-jobs-scraper", "max_results": 50},
            is_active=True,
            last_synced_at=days_ago(1),
        ),
        JobSource(
            name="Greenhouse Job Board",
            connector_type="greenhouse",
            config={"board_token": "acme"},
            is_active=True,
            last_synced_at=days_ago(2),
        ),
        JobSource(
            name="Lever Job Board",
            connector_type="lever",
            config={"company": "openai"},
            is_active=True,
            last_synced_at=days_ago(3),
        ),
        JobSource(
            name="Company Careers Pages",
            connector_type="custom_scraper",
            config={"urls": ["https://careers.anthropic.com", "https://deepmind.google/careers"]},
            is_active=True,
            last_synced_at=days_ago(1),
        ),
        JobSource(
            name="HackerNews Who's Hiring",
            connector_type="hn_hiring",
            config={"month": "March 2026"},
            is_active=False,
            last_synced_at=days_ago(14),
        ),
    ]
    for src in sources:
        session.add(src)
    await session.flush()

    # ── Jobs ─────────────────────────────────────────────────────────────────
    print(f"   Creating {len(JOB_LISTINGS)} job postings...")
    jobs = []
    source_cycle = [sources[0], sources[1], sources[2], sources[3]]
    for i, listing in enumerate(JOB_LISTINGS):
        source_job_id = (
            f"{listing['company_name'].lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        )
        salary_text = None
        if listing.get("salary_min"):
            salary_text = (
                f"${listing['salary_min']:,}–${listing['salary_max']:,} "
                f"{listing.get('currency', 'USD')}"
            )
        apply_url = (
            f"https://jobs.{listing['company_name'].lower().replace(' ', '')}.com/apply/"
            f"{uuid.uuid4().hex[:8]}"
        )
        job = Job(
            source_id=source_cycle[i % len(source_cycle)].id,
            source_job_id=source_job_id,
            company_name=listing["company_name"],
            title=listing["title"],
            location=listing.get("location"),
            is_remote=listing.get("is_remote", False),
            is_hybrid=listing.get("is_hybrid", False),
            is_onsite=listing.get("is_onsite", False),
            employment_type=listing.get("employment_type", EmploymentType.full_time),
            seniority=listing.get("seniority", JobSeniority.mid),
            salary_min=listing.get("salary_min"),
            salary_max=listing.get("salary_max"),
            salary_text=salary_text,
            currency=listing.get("currency", "USD"),
            raw_description=listing.get("raw_description"),
            cleaned_description=listing.get("raw_description"),
            requirements=listing.get("requirements", []),
            responsibilities=listing.get("responsibilities", []),
            preferred_qualifications=listing.get("preferred_qualifications", []),
            apply_url=apply_url,
            posting_date=days_ago(random.randint(1, 30)),
            status=JobStatus.active,
        )
        jobs.append(job)
        session.add(job)

    await session.flush()

    # ── Job Matches ──────────────────────────────────────────────────────────
    print("   Computing job match scores...")
    # Define realistic scores based on role relevance
    match_scores = [
        (0.94, 0.96, 0.92),  # OpenMind AI — very strong match
        (0.91, 0.93, 0.89),  # Anthropic — strong match
        (0.88, 0.90, 0.86),  # Meta AI
        (0.85, 0.87, 0.83),  # DeepMind
        (0.92, 0.94, 0.90),  # Stripe Staff
        (0.79, 0.82, 0.76),  # Adobe — good
        (0.76, 0.79, 0.73),  # Cohere
        (0.81, 0.84, 0.78),  # Mistral
        (0.83, 0.86, 0.80),  # Airbnb
        (0.77, 0.80, 0.74),  # Hugging Face
        (0.74, 0.78, 0.70),  # Elastic
        (0.68, 0.72, 0.64),  # Apple — onsite, lower fit
        (0.80, 0.83, 0.77),  # Spotify
        (0.87, 0.89, 0.85),  # Stealth Startup
        (0.78, 0.81, 0.75),  # Scale AI
        (0.65, 0.70, 0.60),  # Waymo — very different domain
        (0.72, 0.75, 0.69),  # Amazon Alexa
        (0.84, 0.87, 0.81),  # Together AI
        (0.86, 0.88, 0.84),  # Databricks
        (0.89, 0.91, 0.87),  # Perplexity
        (0.55, 0.60, 0.50),  # Google intern (low — overqualified)
        (0.70, 0.73, 0.67),  # Snowflake contract
        (0.73, 0.76, 0.70),  # Notion
        (0.71, 0.74, 0.68),  # Roblox
        (0.78, 0.81, 0.75),  # Stability AI
    ]

    for job, (total, emb_sim, kw_score) in zip(jobs, match_scores):
        match = JobMatch(
            job_id=job.id,
            user_id=user.id,
            match_score=total,
            embedding_similarity=emb_sim,
            keyword_overlap_score=kw_score,
            seniority_fit=random.uniform(0.7, 1.0),
            location_fit=1.0 if job.is_remote else random.uniform(0.5, 0.9),
            skill_matches=random.sample(SKILLS, min(8, len(SKILLS))),
            skill_gaps=random.sample(["CUDA", "C++", "Scala", "Go", "Java"], random.randint(0, 2)),
            strengths=[
                "Strong Python background",
                "Relevant ML experience",
                "Product-oriented mindset",
            ],
            weaknesses=["Limited publications" if "Research" in job.title else "No major gap"],
            explanation=(
                f"Strong match for {job.title} at {job.company_name}. "
                f"Your Python + PyTorch + LLM experience aligns with the role. "
                f"Match score: {total:.0%}."
            ),
            model_used="gpt-4o",
            prompt_version="v1.2",
        )
        session.add(match)

    await session.flush()

    # ── Applications ─────────────────────────────────────────────────────────
    print("   Creating 8 applications in various statuses...")
    app_configs = [
        (jobs[0], ApplicationStatus.interview_scheduled, days_ago(5)),
        (jobs[1], ApplicationStatus.applied, days_ago(10)),
        (jobs[2], ApplicationStatus.recruiter_contacted, days_ago(8)),
        (jobs[4], ApplicationStatus.offer, days_ago(20)),
        (jobs[5], ApplicationStatus.tailored, days_ago(3)),
        (jobs[6], ApplicationStatus.shortlisted, days_ago(2)),
        (jobs[14], ApplicationStatus.rejected, days_ago(15)),
        (jobs[19], ApplicationStatus.applied, days_ago(7)),
    ]

    applications = []
    for job, status, applied_at in app_configs:
        app = Application(
            user_id=user.id,
            job_id=job.id,
            status=status,
            applied_at=applied_at
            if status
            in (
                ApplicationStatus.applied,
                ApplicationStatus.offer,
                ApplicationStatus.interview_scheduled,
                ApplicationStatus.rejected,
                ApplicationStatus.recruiter_contacted,
                ApplicationStatus.oa_received,
            )
            else None,
            notes="Applied via company website. Job looks like an excellent fit.",
            source_of_discovery="Apify LinkedIn Scraper",
        )
        applications.append(app)
        session.add(app)

    await session.flush()

    # Application events (audit trail)
    status_progression = {
        ApplicationStatus.interview_scheduled: [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
            ApplicationStatus.applied,
            ApplicationStatus.recruiter_contacted,
            ApplicationStatus.interview_scheduled,
        ],
        ApplicationStatus.applied: [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
            ApplicationStatus.applied,
        ],
        ApplicationStatus.recruiter_contacted: [
            ApplicationStatus.discovered,
            ApplicationStatus.applied,
            ApplicationStatus.recruiter_contacted,
        ],
        ApplicationStatus.offer: [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
            ApplicationStatus.applied,
            ApplicationStatus.recruiter_contacted,
            ApplicationStatus.interview_scheduled,
            ApplicationStatus.offer,
        ],
        ApplicationStatus.tailored: [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
            ApplicationStatus.tailored,
        ],
        ApplicationStatus.shortlisted: [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
        ],
        ApplicationStatus.rejected: [
            ApplicationStatus.discovered,
            ApplicationStatus.applied,
            ApplicationStatus.rejected,
        ],
    }

    for app, (_, status, applied_at) in zip(applications, app_configs):
        steps = status_progression.get(status, [ApplicationStatus.discovered, status])
        prev = None
        for i, step in enumerate(steps):
            event = ApplicationEvent(
                application_id=app.id,
                from_status=prev,
                to_status=step,
                triggered_by=TriggeredBy.user
                if i == 0
                else (
                    TriggeredBy.email_parser
                    if step == ApplicationStatus.recruiter_contacted
                    else TriggeredBy.user
                ),
                notes=f"Transitioned to {step.value}",
            )
            session.add(event)
            prev = step

    await session.flush()

    # Resume versions for the top 3 applications
    print("   Creating tailored resume versions...")
    for i, (app, (job, status, _)) in enumerate(zip(applications[:3], app_configs[:3])):
        rv = ResumeVersion(
            user_id=user.id,
            master_resume_id=master_resume.id,
            application_id=app.id,
            job_id=job.id,
            name=f"Resume for {job.company_name} — {job.title}",
            tailored_content=(
                f"ALEX CHEN — Tailored for {job.company_name}\n\n"
                "Highlights aligned to role: "
                + ", ".join(job.requirements[:3] if job.requirements else ["ML", "Python"])
            ),
            tailored_data={"highlights": job.requirements[:3] if job.requirements else []},
            tailoring_strategy={
                "approach": "keyword_injection + reorder_bullets",
                "changes": [
                    "Added company-specific language",
                    "Reordered bullet points by relevance",
                ],
            },
            ai_model_used="gpt-4o",
            prompt_version="v1.2",
        )
        session.add(rv)

    await session.flush()

    # ── Email Threads ─────────────────────────────────────────────────────────
    print("   Creating email threads and parsed emails...")

    # Thread 1: Recruiter outreach for interview_scheduled application
    app_interview = applications[0]
    job_interview = jobs[0]

    thread1 = EmailThread(
        user_id=user.id,
        application_id=app_interview.id,
        thread_id=f"gmail-thread-{uuid.uuid4().hex[:16]}",
        subject=f"Interview invitation — {job_interview.title} at {job_interview.company_name}",
        participants=["recruiter@openmindai.com", DEMO_EMAIL],
        last_message_at=days_ago(2),
        message_count=3,
        classification=EmailClassification.interview_scheduling,
        confidence_score=0.97,
    )
    session.add(thread1)
    await session.flush()

    session.add(
        ParsedEmail(
            thread_id=thread1.id,
            user_id=user.id,
            message_id=f"msg-{uuid.uuid4().hex[:16]}",
            subject=thread1.subject,
            sender_email="recruiter@openmindai.com",
            sender_name="Sarah Park",
            received_at=days_ago(3),
            raw_body=(
                "Hi Alex, I'm Sarah from OpenMind AI's talent team. We reviewed your profile "
                "and would love to schedule a technical interview for our Senior ML Engineer role. "
                "Are you available next week? Best, Sarah"
            ),
            cleaned_body="Recruiter outreach for Senior ML Engineer role at OpenMind AI.",
            classification=EmailClassification.interview_scheduling,
            confidence_score=0.97,
            extracted_company="OpenMind AI",
            extracted_job_title="Senior ML Engineer",
            extracted_interviewer_name="Sarah Park",
            extracted_interview_datetime=days_from_now(5),
            extracted_timezone="America/Los_Angeles",
            extracted_meeting_link="https://zoom.us/j/123456789",
            extracted_next_action="Confirm interview slot",
            model_used="gpt-4o",
            prompt_version="v1.1",
        )
    )

    # Thread 2: OA received
    app_oa = applications[1]
    job_oa = jobs[1]

    thread2 = EmailThread(
        user_id=user.id,
        application_id=app_oa.id,
        thread_id=f"gmail-thread-{uuid.uuid4().hex[:16]}",
        subject=f"Online Assessment — {job_oa.title} at {job_oa.company_name}",
        participants=["recruiting@anthropic.com", DEMO_EMAIL],
        last_message_at=days_ago(6),
        message_count=2,
        classification=EmailClassification.oa_assessment,
        confidence_score=0.94,
    )
    session.add(thread2)
    await session.flush()

    session.add(
        ParsedEmail(
            thread_id=thread2.id,
            user_id=user.id,
            message_id=f"msg-{uuid.uuid4().hex[:16]}",
            subject=thread2.subject,
            sender_email="recruiting@anthropic.com",
            sender_name="Anthropic Recruiting",
            received_at=days_ago(7),
            raw_body=(
                "Dear Alex, thank you for applying to the AI Engineer position at Anthropic. "
                "Please complete the following online assessment within 5 days. "
                "Link: https://assessments.anthropic.com/alex123"
            ),
            cleaned_body="OA invitation from Anthropic for AI Engineer role.",
            classification=EmailClassification.oa_assessment,
            confidence_score=0.94,
            extracted_company="Anthropic",
            extracted_job_title="AI Engineer — Agents & Tooling",
            extracted_next_action="Complete online assessment within 5 days",
            extracted_data={
                "assessment_link": "https://assessments.anthropic.com/alex123",
                "deadline_days": 5,
            },
            model_used="gpt-4o",
            prompt_version="v1.1",
        )
    )

    # Thread 3: Rejection
    app_rejected = applications[6]

    thread3 = EmailThread(
        user_id=user.id,
        application_id=app_rejected.id,
        thread_id=f"gmail-thread-{uuid.uuid4().hex[:16]}",
        subject="Your application to Scale AI",
        participants=["noreply@scaleai.com", DEMO_EMAIL],
        last_message_at=days_ago(14),
        message_count=1,
        classification=EmailClassification.rejection,
        confidence_score=0.99,
    )
    session.add(thread3)
    await session.flush()

    session.add(
        ParsedEmail(
            thread_id=thread3.id,
            user_id=user.id,
            message_id=f"msg-{uuid.uuid4().hex[:16]}",
            subject="Your application to Scale AI",
            sender_email="noreply@scaleai.com",
            sender_name="Scale AI Recruiting",
            received_at=days_ago(14),
            raw_body=(
                "Hi Alex, thank you for your interest in the ML Research Engineer position "
                "at Scale AI. After careful consideration, we've decided to move forward with "
                "other candidates at this time. We encourage you to apply again in the future."
            ),
            cleaned_body="Rejection email from Scale AI.",
            classification=EmailClassification.rejection,
            confidence_score=0.99,
            extracted_company="Scale AI",
            extracted_job_title="ML Research Engineer — Vision",
            model_used="gpt-4o",
            prompt_version="v1.1",
        )
    )

    await session.flush()

    # ── Calendar Events ───────────────────────────────────────────────────────
    print("   Creating calendar events...")

    # Event 1: Upcoming technical screen
    cal1 = CalendarEvent(
        user_id=user.id,
        application_id=app_interview.id,
        title=f"Technical Screen — {job_interview.company_name}",
        description=(
            f"Technical interview for {job_interview.title} role.\n"
            "Topics: ML fundamentals, system design, coding.\n"
            "Interviewer: Sarah Park (Engineering Lead)"
        ),
        start_datetime=days_from_now(5).replace(hour=14, minute=0, second=0, microsecond=0),
        end_datetime=days_from_now(5).replace(hour=15, minute=0, second=0, microsecond=0),
        timezone="America/Los_Angeles",
        meeting_link="https://zoom.us/j/123456789",
        location=None,
        status=CalendarEventStatus.confirmed,
        google_event_id=f"google-cal-event-{uuid.uuid4().hex[:16]}",
        reminder_minutes=[30, 60, 1440],  # 30min, 1hr, 1day before
    )
    session.add(cal1)

    # Event 2: Offer discussion call
    app_offer = applications[3]
    job_offer = jobs[4]
    cal2 = CalendarEvent(
        user_id=user.id,
        application_id=app_offer.id,
        title=f"Offer Discussion — {job_offer.company_name}",
        description=(
            f"Call to discuss offer details for {job_offer.title}.\n"
            "Review compensation, equity, and start date."
        ),
        start_datetime=days_from_now(2).replace(hour=10, minute=0, second=0, microsecond=0),
        end_datetime=days_from_now(2).replace(hour=10, minute=30, second=0, microsecond=0),
        timezone="America/New_York",
        meeting_link="https://meet.google.com/abc-defg-hij",
        status=CalendarEventStatus.confirmed,
        google_event_id=f"google-cal-event-{uuid.uuid4().hex[:16]}",
        reminder_minutes=[15, 60],
    )
    session.add(cal2)

    await session.flush()

    # ── Agent Runs ────────────────────────────────────────────────────────────
    print("   Creating agent run records...")
    agent_run_data = [
        (WorkflowName.job_discovery, AgentRunStatus.completed, days_ago(1), 4500, "gpt-4o"),
        (WorkflowName.job_matching, AgentRunStatus.completed, days_ago(1), 2100, "gpt-4o"),
        (
            WorkflowName.resume_tailoring,
            AgentRunStatus.completed,
            days_ago(5),
            6800,
            "claude-3-5-sonnet-20241022",
        ),
        (
            WorkflowName.email_classification,
            AgentRunStatus.completed,
            days_ago(2),
            350,
            "gpt-4o-mini",
        ),
        (WorkflowName.email_extraction, AgentRunStatus.completed, days_ago(2), 500, "gpt-4o"),
        (
            WorkflowName.calendar_automation,
            AgentRunStatus.completed,
            days_ago(2),
            200,
            "gpt-4o-mini",
        ),
        (WorkflowName.resume_tailoring, AgentRunStatus.failed, days_ago(3), None, "gpt-4o"),
    ]

    for wf, status, created, tokens, model in agent_run_data:
        run = AgentRun(
            user_id=user.id,
            workflow_name=wf,
            status=status,
            input_data={"user_id": str(user.id), "workflow": wf.value},
            output_data={"success": status == AgentRunStatus.completed}
            if status != AgentRunStatus.failed
            else None,
            error_message="Rate limit exceeded" if status == AgentRunStatus.failed else None,
            model_used=model,
            prompt_version="v1.2",
            tokens_used=tokens,
            duration_ms=random.randint(500, 8000),
            started_at=created,
            completed_at=created + timedelta(seconds=random.randint(2, 30))
            if status == AgentRunStatus.completed
            else None,
        )
        session.add(run)

    await session.flush()

    # ── Commit ───────────────────────────────────────────────────────────────
    await session.commit()
    print("\n✅  Seed complete!")
    print(f"   Demo credentials: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print("   Users created:    1")
    print(f"   Jobs created:     {len(jobs)}")
    print(f"   Applications:     {len(applications)}")
    print("   Email threads:    3")
    print("   Calendar events:  2")
    print(f"   Agent runs:       {len(agent_run_data)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
