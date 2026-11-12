"""Evidence-grounded content generation and resume/job analysis."""
from __future__ import annotations

import re
from collections import Counter

from flask import current_app

from app.ai import llm
from app.ai.rag_service import STOPWORDS, retrieve
from app.extensions import db
from app.models import AIGeneration, Profile, Project, ResearchProject, Skill

KIND_LABELS = {
    "project_description": "project description",
    "technical_summary": "technical summary",
    "blog_draft": "blog draft outline",
    "linkedin_post": "LinkedIn post",
    "certificate_description": "certificate description",
    "portfolio_summary": "portfolio summary",
    "resume_summary": "resume summary",
}

GENERATION_PROMPT = """You write content for Muwagamage Tharushi Prabhasha Dilshani's portfolio.
Use ONLY the supplied verified context. Do not invent employers, dates, certificates, awards,
metrics, or experience. If a detail is missing, omit it or use a clear placeholder such as
"[add verified detail]" instead of guessing. Return clean Markdown with no preamble.
"""


def _verified_context(extra: str = "") -> str:
    profile = Profile.query.order_by(Profile.id.asc()).first()
    parts = []
    if profile:
        parts.append(
            f"Name: {profile.full_name}\nTitle: {profile.professional_title}\n"
            f"Summary: {profile.summary}\nLocation: {profile.location or ''}\n"
            f"Career goals: {profile.career_goals or ''}"
        )
    skills = Skill.query.filter_by(is_visible=True).all()
    if skills:
        parts.append("Skills: " + ", ".join(skill.name for skill in skills))
    for project in Project.query.filter_by(status="published", is_deleted=False).all():
        parts.append(f"Project: {project.title} - {project.short_description}")
    for research in ResearchProject.query.filter_by(status="published", is_deleted=False).all():
        parts.append(f"Research: {research.title} - {research.abstract or ''}")
    if extra:
        parts.append(f"Additional supplied context:\n{extra}")
    return "\n\n".join(parts)


def _template_output(kind: str, prompt: str, context: str) -> str:
    label = KIND_LABELS.get(kind, kind.replace("_", " "))
    sources = retrieve(prompt, top_k=4)
    evidence = "\n".join(f"- {source['title']}: {' '.join(source['content'].split())[:240]}" for source in sources)
    return (
        f"## {label.title()} draft\n\n"
        f"**Request:** {prompt}\n\n"
        "**Verified material used**\n"
        f"{evidence or '- No matching verified portfolio records were found for this request.'}\n\n"
        "**Draft**\n"
        f"Write the final {label} using only the verified material above. "
        "Add `[add verified detail]` wherever a fact is missing.\n\n"
        "> Generated with the local template fallback because no LLM API key is configured."
    )


def generate_content(kind: str, prompt: str, context: str, user_id: int | None = None) -> dict:
    verified = _verified_context(context or "")
    result = llm.complete(
        [
            {
                "role": "user",
                "content": f"KIND: {kind}\n\nVERIFIED CONTEXT:\n{verified}\n\nREQUEST:\n{prompt}",
            }
        ],
        system=GENERATION_PROMPT,
        temperature=0.4,
        max_tokens=900,
    )
    output = result.text if result.ok else _template_output(kind, prompt, context)
    record = AIGeneration(
        kind=kind,
        prompt=prompt,
        output=output,
        status="draft",
        provider=result.provider if result.ok else "template",
        model=result.model,
        created_by=user_id,
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict()


def _keywords(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9][a-z0-9+#.]*", (text or "").lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def analyze_resume(job_description: str, role_family: str | None = None, user_id: int | None = None) -> dict:
    keyword_counts = Counter(_keywords(job_description))
    expected = {keyword for keyword, _count in keyword_counts.most_common(40)}

    portfolio_parts = [_verified_context()]
    skills = {skill.name.lower() for skill in Skill.query.filter_by(is_visible=True).all()}
    projects = [project.title for project in Project.query.filter_by(status="published", is_deleted=False).all()]
    portfolio_parts.extend(projects)
    portfolio_tokens = _keywords("\n".join(portfolio_parts)) | skills

    matched = sorted(expected & portfolio_tokens)
    missing = sorted(expected - portfolio_tokens)
    match_ratio = round(len(matched) / max(1, len(expected)) * 100, 1)

    summary = (
        f"## Job match analysis{f' - {role_family}' if role_family else ''}\n\n"
        f"**Keyword coverage:** {match_ratio}% ({len(matched)}/{len(expected)} key terms matched)\n\n"
        f"**Matched evidence:** {', '.join(matched) or 'none detected'}\n\n"
        f"**Gaps to address honestly:** {', '.join(missing) or 'none detected'}\n\n"
        "**Suggestion:** Emphasise only the matched, verified projects and skills. Do not add "
        "experience or tools that are not present in the portfolio. Use `[add verified detail]` "
        "for anything missing.\n"
    )

    result = llm.complete(
        [
            {
                "role": "user",
                "content": (
                    "Compare this verified portfolio against the job description. Produce a concise "
                    "match summary, strongest verified evidence, honest gaps, and a 120-word tailored "
                    f"profile summary.\n\nJOB DESCRIPTION:\n{job_description}\n\nPORTFOLIO:\n{_verified_context()}"
                ),
            }
        ],
        system=GENERATION_PROMPT,
        temperature=0.2,
        max_tokens=900,
    )
    output = f"{summary}\n\n## Tailored summary\n\n{result.text}" if result.ok else summary
    record = AIGeneration(
        kind="resume_analysis",
        prompt=job_description[:4000],
        output=output,
        status="draft",
        provider=result.provider if result.ok else "template",
        model=result.model,
        created_by=user_id,
    )
    db.session.add(record)
    db.session.commit()
    data = record.to_dict()
    data["matched_keywords"] = matched
    data["missing_keywords"] = missing
    data["match_ratio"] = match_ratio
    return data


def review_generation(generation_id: int, status: str) -> dict:
    record = db.session.get(AIGeneration, generation_id)
    if record is None:
        return {}
    record.status = status
    db.session.commit()
    return record.to_dict()
