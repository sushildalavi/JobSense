"""
Resume service — CRUD, parsing, PDF export.
"""

from __future__ import annotations

import io
import json
import uuid
from typing import List, Optional

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import MasterResume, ResumeVersion
from app.schemas.resume import MasterResumeUpdate, ParsedResumeData

logger = structlog.get_logger(__name__)


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Master resumes ────────────────────────────────────────────────────────

    async def list_resumes(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[MasterResume]:
        result = await self.db.execute(
            select(MasterResume)
            .where(MasterResume.user_id == user_id, MasterResume.is_active.is_(True))
            .order_by(MasterResume.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_master_resume(
        self,
        user_id: uuid.UUID,
        file: UploadFile,
        name: str,
    ) -> MasterResume:
        """Store resume file, extract text, return MasterResume record."""
        content = await file.read()
        raw_text = await self._extract_text(file.filename or "", content)

        # Try to upload to storage if configured
        file_url: Optional[str] = None
        try:
            from app.core.storage_utils import upload_file

            file_url = await upload_file(
                file_bytes=content,
                key=f"resumes/{user_id}/{uuid.uuid4()}/{file.filename}",
                content_type=file.content_type or "application/octet-stream",
            )
        except Exception as exc:
            logger.warning("File upload skipped", error=str(exc))

        resume = MasterResume(
            user_id=user_id,
            name=name,
            raw_text=raw_text,
            file_url=file_url,
            file_name=file.filename,
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def get_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> MasterResume:
        result = await self.db.execute(
            select(MasterResume).where(
                MasterResume.id == resume_id,
                MasterResume.user_id == user_id,
            )
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        return resume

    async def update_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MasterResumeUpdate,
    ) -> MasterResume:
        resume = await self.get_resume(resume_id, user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(resume, field, value)
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def delete_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> None:
        resume = await self.get_resume(resume_id, user_id)
        resume.is_active = False
        self.db.add(resume)
        await self.db.commit()

    async def trigger_parse(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> MasterResume:
        """Run AI text parsing and store structured data on the resume."""
        resume = await self.get_resume(resume_id, user_id)
        if resume.raw_text:
            parsed = await self.parse_resume_text(resume.raw_text)
            resume.parsed_data = parsed.model_dump()
            self.db.add(resume)
            await self.db.commit()
            await self.db.refresh(resume)
        return resume

    # ── Versions ──────────────────────────────────────────────────────────────

    async def get_resume_versions(
        self, resume_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[ResumeVersion]:
        result = await self.db.execute(
            select(ResumeVersion)
            .where(
                ResumeVersion.master_resume_id == resume_id,
                ResumeVersion.user_id == user_id,
            )
            .order_by(ResumeVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, version_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        result = await self.db.execute(
            select(ResumeVersion).where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
            )
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found"
            )
        return version

    async def create_resume_version(
        self,
        master_resume_id: uuid.UUID,
        user_id: uuid.UUID,
        job_id: Optional[uuid.UUID],
        application_id: Optional[uuid.UUID],
        tailored_content: str,
        strategy: Optional[dict],
        model_used: Optional[str] = None,
        prompt_version: Optional[str] = None,
    ) -> ResumeVersion:
        master = await self.db.get(MasterResume, master_resume_id)
        name = f"Tailored — {master.name}" if master else "Tailored Resume"
        version = ResumeVersion(
            user_id=user_id,
            master_resume_id=master_resume_id,
            job_id=job_id,
            application_id=application_id,
            name=name,
            tailored_content=tailored_content,
            tailoring_strategy=strategy,
            ai_model_used=model_used,
            prompt_version=prompt_version,
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def export_version_to_pdf(self, version_id: uuid.UUID, user_id: uuid.UUID) -> bytes:
        """Generate a minimal PDF from the tailored content."""
        version = await self.get_version(version_id, user_id)
        return self._render_pdf(version.tailored_content or "")

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _extract_text(self, filename: str, content: bytes) -> str:
        """Extract plain text from PDF or DOCX files."""
        lower = filename.lower()
        try:
            if lower.endswith(".pdf"):
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(content))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages)
            elif lower.endswith(".docx"):
                from docx import Document

                doc = Document(io.BytesIO(content))
                return "\n".join(para.text for para in doc.paragraphs)
            else:
                # Try decoding as plain text
                return content.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Text extraction failed", error=str(exc), filename=filename)
            return ""

    async def parse_resume_text(self, text: str) -> ParsedResumeData:
        """Use an LLM to extract structured data from resume text."""
        try:
            from app.agents.llm import get_llm
            from app.agents.prompts import RESUME_PARSE_PROMPT_V1
            from app.core.config import settings

            llm = get_llm(settings.DEFAULT_LLM_PROVIDER)
            prompt = RESUME_PARSE_PROMPT_V1.format(resume_text=text[:8000])
            response = await llm.ainvoke(prompt)
            raw = response.content if hasattr(response, "content") else str(response)

            # Strip markdown fences
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            data = json.loads(raw)
            return ParsedResumeData(**data)
        except Exception as exc:
            logger.warning("Resume parsing failed", error=str(exc))
            return ParsedResumeData()

    def _render_pdf(self, content: str) -> bytes:
        """Render resume text content to PDF bytes using reportlab."""
        try:
            import io as _io

            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

            buf = _io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            for line in content.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
                    story.append(Spacer(1, 4))
            doc.build(story)
            return buf.getvalue()
        except ImportError:
            # Fallback: return content as UTF-8 bytes prefixed with a minimal marker
            logger.warning("reportlab not installed; returning plain text bytes")
            return content.encode("utf-8")
