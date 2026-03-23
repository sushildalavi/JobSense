"""Initial schema — creates all JobSense tables, enums, and indexes.

Revision ID: 001
Revises:
Create Date: 2026-03-16 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Extensions
    # =========================================================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # =========================================================================
    # Enums
    # =========================================================================

    # Profile enums
    remote_preference_enum = postgresql.ENUM(
        "remote",
        "hybrid",
        "onsite",
        "flexible",
        name="remote_preference_enum",
        create_type=False,
    )
    remote_preference_enum.create(op.get_bind(), checkfirst=True)

    seniority_level_enum = postgresql.ENUM(
        "intern",
        "junior",
        "mid",
        "senior",
        "staff",
        "principal",
        "director",
        "vp",
        "c_level",
        name="seniority_level_enum",
        create_type=False,
    )
    seniority_level_enum.create(op.get_bind(), checkfirst=True)

    # Job enums
    employment_type_enum = postgresql.ENUM(
        "full_time",
        "part_time",
        "contract",
        "internship",
        "freelance",
        name="employment_type_enum",
        create_type=False,
    )
    employment_type_enum.create(op.get_bind(), checkfirst=True)

    job_seniority_enum = postgresql.ENUM(
        "intern",
        "junior",
        "mid",
        "senior",
        "staff",
        "principal",
        "director",
        "vp",
        "c_level",
        name="job_seniority_enum",
        create_type=False,
    )
    job_seniority_enum.create(op.get_bind(), checkfirst=True)

    job_status_enum = postgresql.ENUM(
        "active",
        "expired",
        "removed",
        name="job_status_enum",
        create_type=False,
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)

    # Application enums
    application_status_enum = postgresql.ENUM(
        "discovered",
        "shortlisted",
        "tailored",
        "ready_to_apply",
        "applied",
        "oa_received",
        "recruiter_contacted",
        "interview_scheduled",
        "rejected",
        "offer",
        "archived",
        name="application_status_enum",
        create_type=False,
    )
    application_status_enum.create(op.get_bind(), checkfirst=True)

    triggered_by_enum = postgresql.ENUM(
        "user",
        "email_parser",
        "agent",
        "automation",
        name="triggered_by_enum",
        create_type=False,
    )
    triggered_by_enum.create(op.get_bind(), checkfirst=True)

    # Document enums
    document_type_enum = postgresql.ENUM(
        "master_resume",
        "tailored_resume",
        "cover_letter",
        "portfolio",
        "other",
        name="document_type_enum",
        create_type=False,
    )
    document_type_enum.create(op.get_bind(), checkfirst=True)

    # Email enums
    email_classification_enum = postgresql.ENUM(
        "recruiter_outreach",
        "oa_assessment",
        "interview_scheduling",
        "interview_confirmation",
        "rejection",
        "offer",
        "follow_up",
        "noise",
        "unclassified",
        name="email_classification_enum",
        create_type=False,
    )
    email_classification_enum.create(op.get_bind(), checkfirst=True)

    # Calendar enums
    calendar_event_status_enum = postgresql.ENUM(
        "pending",
        "confirmed",
        "cancelled",
        name="calendar_event_status_enum",
        create_type=False,
    )
    calendar_event_status_enum.create(op.get_bind(), checkfirst=True)

    # Agent enums
    workflow_name_enum = postgresql.ENUM(
        "job_discovery",
        "job_matching",
        "resume_tailoring",
        "email_classification",
        "email_extraction",
        "calendar_automation",
        "follow_up_draft",
        name="workflow_name_enum",
        create_type=False,
    )
    workflow_name_enum.create(op.get_bind(), checkfirst=True)

    agent_run_status_enum = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="agent_run_status_enum",
        create_type=False,
    )
    agent_run_status_enum.create(op.get_bind(), checkfirst=True)

    session_type_enum = postgresql.ENUM(
        "form_fill",
        "resume_upload",
        "survey",
        "other",
        name="session_type_enum",
        create_type=False,
    )
    session_type_enum.create(op.get_bind(), checkfirst=True)

    session_status_enum = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="session_status_enum",
        create_type=False,
    )
    session_status_enum.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Table: users
    # =========================================================================
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.Text, nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("google_tokens", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # =========================================================================
    # Table: profiles
    # =========================================================================
    op.create_table(
        "profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_roles", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_locations", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "remote_preference",
            postgresql.ENUM(
                "remote",
                "hybrid",
                "onsite",
                "flexible",
                name="remote_preference_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "seniority_level",
            postgresql.ENUM(
                "intern",
                "junior",
                "mid",
                "senior",
                "staff",
                "principal",
                "director",
                "vp",
                "c_level",
                name="seniority_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("preferred_industries", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("years_of_experience", sa.Integer, nullable=True),
        sa.Column("visa_status", sa.String(100), nullable=True),
        sa.Column("work_authorization", sa.String(100), nullable=True),
        sa.Column("preferred_salary_min", sa.Integer, nullable=True),
        sa.Column("preferred_salary_max", sa.Integer, nullable=True),
        sa.Column("preferred_currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords_to_prioritize", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords_to_avoid", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("github_url", sa.String(512), nullable=True),
        sa.Column("portfolio_url", sa.String(512), nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)
    op.create_index("ix_profiles_created_at", "profiles", ["created_at"])

    # =========================================================================
    # Table: master_resumes
    # =========================================================================
    op.create_table(
        "master_resumes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("parsed_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("file_url", sa.Text, nullable=True),
        sa.Column("file_name", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_master_resumes_user_id", "master_resumes", ["user_id"])
    op.create_index("ix_master_resumes_created_at", "master_resumes", ["created_at"])

    # =========================================================================
    # Table: job_sources
    # =========================================================================
    op.create_table(
        "job_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("connector_type", sa.String(100), nullable=False),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_job_sources_name", "job_sources", ["name"], unique=True)

    # =========================================================================
    # Table: job_dedup_clusters  (referenced by jobs; must exist first)
    # =========================================================================
    op.create_table(
        "job_dedup_clusters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        # canonical_job_id FK is added after jobs table exists
        sa.Column(
            "canonical_job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("member_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_job_dedup_clusters_canonical_job_id", "job_dedup_clusters", ["canonical_job_id"]
    )

    # =========================================================================
    # Table: jobs
    # =========================================================================
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_job_id", sa.String(512), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("company_website", sa.Text, nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_hybrid", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_onsite", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "employment_type",
            postgresql.ENUM(
                "full_time",
                "part_time",
                "contract",
                "internship",
                "freelance",
                name="employment_type_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "seniority",
            postgresql.ENUM(
                "intern",
                "junior",
                "mid",
                "senior",
                "staff",
                "principal",
                "director",
                "vp",
                "c_level",
                name="job_seniority_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("salary_text", sa.String(512), nullable=True),
        sa.Column("salary_min", sa.Integer, nullable=True),
        sa.Column("salary_max", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("raw_description", sa.Text, nullable=True),
        sa.Column("cleaned_description", sa.Text, nullable=True),
        sa.Column("requirements", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "preferred_qualifications", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("responsibilities", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("apply_url", sa.Text, nullable=True),
        sa.Column("posting_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "expired",
                "removed",
                name="job_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "dedup_cluster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_dedup_clusters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # unique constraint
        sa.UniqueConstraint("source_id", "source_job_id", name="uq_job_source_job_id"),
    )
    op.create_index("ix_jobs_source_id", "jobs", ["source_id"])
    op.create_index("ix_jobs_source_job_id", "jobs", ["source_job_id"])
    op.create_index("ix_jobs_company_name", "jobs", ["company_name"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_dedup_cluster_id", "jobs", ["dedup_cluster_id"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])

    # Now that jobs exists we can add the FK on job_dedup_clusters
    op.create_foreign_key(
        "fk_job_dedup_clusters_canonical_job_id",
        "job_dedup_clusters",
        "jobs",
        ["canonical_job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # =========================================================================
    # Table: job_cluster_members
    # =========================================================================
    op.create_table(
        "job_cluster_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "cluster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_dedup_clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("similarity_score", sa.Float, nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_job_cluster_members_cluster_id", "job_cluster_members", ["cluster_id"])
    op.create_index("ix_job_cluster_members_job_id", "job_cluster_members", ["job_id"])

    # =========================================================================
    # Table: job_matches
    # =========================================================================
    op.create_table(
        "job_matches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("embedding_similarity", sa.Float, nullable=True),
        sa.Column("keyword_overlap_score", sa.Float, nullable=True),
        sa.Column("seniority_fit", sa.Float, nullable=True),
        sa.Column("location_fit", sa.Float, nullable=True),
        sa.Column("skill_matches", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("skill_gaps", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("strengths", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("weaknesses", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.UniqueConstraint("job_id", "user_id", name="uq_job_match_job_user"),
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index("ix_job_matches_match_score", "job_matches", ["match_score"])

    # =========================================================================
    # Table: applications
    # =========================================================================
    op.create_table(
        "applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # resume_version_id FK added after resume_versions table is created
        sa.Column(
            "resume_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "discovered",
                "shortlisted",
                "tailored",
                "ready_to_apply",
                "applied",
                "oa_received",
                "recruiter_contacted",
                "interview_scheduled",
                "rejected",
                "offer",
                "archived",
                name="application_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="discovered",
        ),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("custom_answers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("application_url", sa.Text, nullable=True),
        sa.Column("source_of_discovery", sa.String(255), nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_created_at", "applications", ["created_at"])

    # =========================================================================
    # Table: resume_versions  (depends on applications)
    # =========================================================================
    op.create_table(
        "resume_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "master_resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("master_resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tailored_content", sa.Text, nullable=True),
        sa.Column("tailored_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("tailoring_strategy", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_model_used", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("pdf_url", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_resume_versions_user_id", "resume_versions", ["user_id"])
    op.create_index("ix_resume_versions_master_resume_id", "resume_versions", ["master_resume_id"])
    op.create_index("ix_resume_versions_application_id", "resume_versions", ["application_id"])
    op.create_index("ix_resume_versions_job_id", "resume_versions", ["job_id"])
    op.create_index("ix_resume_versions_created_at", "resume_versions", ["created_at"])

    # Now add the FK from applications.resume_version_id → resume_versions.id
    op.create_foreign_key(
        "fk_applications_resume_version_id",
        "applications",
        "resume_versions",
        ["resume_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_applications_resume_version_id", "applications", ["resume_version_id"])

    # =========================================================================
    # Table: application_events
    # =========================================================================
    op.create_table(
        "application_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_status",
            postgresql.ENUM(
                "discovered",
                "shortlisted",
                "tailored",
                "ready_to_apply",
                "applied",
                "oa_received",
                "recruiter_contacted",
                "interview_scheduled",
                "rejected",
                "offer",
                "archived",
                name="application_status_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            postgresql.ENUM(
                "discovered",
                "shortlisted",
                "tailored",
                "ready_to_apply",
                "applied",
                "oa_received",
                "recruiter_contacted",
                "interview_scheduled",
                "rejected",
                "offer",
                "archived",
                name="application_status_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "triggered_by",
            postgresql.ENUM(
                "user",
                "email_parser",
                "agent",
                "automation",
                name="triggered_by_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="user",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_application_events_application_id", "application_events", ["application_id"]
    )
    op.create_index("ix_application_events_created_at", "application_events", ["created_at"])

    # =========================================================================
    # Table: documents
    # =========================================================================
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_type",
            postgresql.ENUM(
                "master_resume",
                "tailored_resume",
                "cover_letter",
                "portfolio",
                "other",
                name="document_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "resume_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_application_id", "documents", ["application_id"])
    op.create_index("ix_documents_resume_version_id", "documents", ["resume_version_id"])

    # =========================================================================
    # Table: email_threads
    # =========================================================================
    op.create_table(
        "email_threads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("subject", sa.Text, nullable=True),
        sa.Column("participants", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "classification",
            postgresql.ENUM(
                "recruiter_outreach",
                "oa_assessment",
                "interview_scheduling",
                "interview_confirmation",
                "rejection",
                "offer",
                "follow_up",
                "noise",
                "unclassified",
                name="email_classification_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="unclassified",
        ),
        sa.Column("confidence_score", sa.Float, nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_email_threads_user_id", "email_threads", ["user_id"])
    op.create_index("ix_email_threads_application_id", "email_threads", ["application_id"])
    op.create_index("ix_email_threads_thread_id", "email_threads", ["thread_id"], unique=True)
    op.create_index("ix_email_threads_classification", "email_threads", ["classification"])
    op.create_index("ix_email_threads_created_at", "email_threads", ["created_at"])

    # =========================================================================
    # Table: parsed_emails
    # =========================================================================
    op.create_table(
        "parsed_emails",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("email_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("subject", sa.Text, nullable=True),
        sa.Column("sender_email", sa.String(320), nullable=True),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_body", sa.Text, nullable=True),
        sa.Column("cleaned_body", sa.Text, nullable=True),
        sa.Column(
            "classification",
            postgresql.ENUM(
                "recruiter_outreach",
                "oa_assessment",
                "interview_scheduling",
                "interview_confirmation",
                "rejection",
                "offer",
                "follow_up",
                "noise",
                "unclassified",
                name="email_classification_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="unclassified",
        ),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("extracted_company", sa.String(255), nullable=True),
        sa.Column("extracted_job_title", sa.String(512), nullable=True),
        sa.Column("extracted_interviewer_name", sa.String(255), nullable=True),
        sa.Column("extracted_interview_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extracted_timezone", sa.String(100), nullable=True),
        sa.Column("extracted_meeting_link", sa.Text, nullable=True),
        sa.Column("extracted_next_action", sa.Text, nullable=True),
        sa.Column("extracted_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_parsed_emails_thread_id", "parsed_emails", ["thread_id"])
    op.create_index("ix_parsed_emails_user_id", "parsed_emails", ["user_id"])
    op.create_index("ix_parsed_emails_message_id", "parsed_emails", ["message_id"], unique=True)

    # =========================================================================
    # Table: calendar_events
    # =========================================================================
    op.create_table(
        "calendar_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "parsed_email_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parsed_emails.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("google_event_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="UTC"),
        sa.Column("meeting_link", sa.Text, nullable=True),
        sa.Column("location", sa.Text, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "confirmed",
                "cancelled",
                name="calendar_event_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reminder_minutes", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])
    op.create_index("ix_calendar_events_application_id", "calendar_events", ["application_id"])
    op.create_index("ix_calendar_events_parsed_email_id", "calendar_events", ["parsed_email_id"])
    op.create_index(
        "ix_calendar_events_google_event_id", "calendar_events", ["google_event_id"], unique=True
    )
    op.create_index("ix_calendar_events_start_datetime", "calendar_events", ["start_datetime"])
    op.create_index("ix_calendar_events_status", "calendar_events", ["status"])

    # =========================================================================
    # Table: agent_runs
    # =========================================================================
    op.create_table(
        "agent_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "workflow_name",
            postgresql.ENUM(
                "job_discovery",
                "job_matching",
                "resume_tailoring",
                "email_classification",
                "email_extraction",
                "calendar_automation",
                "follow_up_draft",
                name="workflow_name_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="agent_run_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("input_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_workflow_name", "agent_runs", ["workflow_name"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_created_at", "agent_runs", ["created_at"])

    # =========================================================================
    # Table: automation_sessions
    # =========================================================================
    op.create_table(
        "automation_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_type",
            postgresql.ENUM(
                "form_fill",
                "resume_upload",
                "survey",
                "other",
                name="session_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="session_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("target_url", sa.Text, nullable=False),
        sa.Column("screenshot_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("action_log", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_automation_sessions_user_id", "automation_sessions", ["user_id"])
    op.create_index(
        "ix_automation_sessions_application_id", "automation_sessions", ["application_id"]
    )
    op.create_index("ix_automation_sessions_status", "automation_sessions", ["status"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("automation_sessions")
    op.drop_table("agent_runs")
    op.drop_table("calendar_events")
    op.drop_table("parsed_emails")
    op.drop_table("email_threads")
    op.drop_table("documents")
    op.drop_table("application_events")
    op.drop_table("resume_versions")
    op.drop_table("applications")
    op.drop_table("job_matches")
    op.drop_table("job_cluster_members")
    op.drop_table("jobs")
    op.drop_table("job_dedup_clusters")
    op.drop_table("job_sources")
    op.drop_table("master_resumes")
    op.drop_table("profiles")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "session_status_enum",
        "session_type_enum",
        "agent_run_status_enum",
        "workflow_name_enum",
        "calendar_event_status_enum",
        "email_classification_enum",
        "document_type_enum",
        "triggered_by_enum",
        "application_status_enum",
        "job_status_enum",
        "job_seniority_enum",
        "employment_type_enum",
        "seniority_level_enum",
        "remote_preference_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
