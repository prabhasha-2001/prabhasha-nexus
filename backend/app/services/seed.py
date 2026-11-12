"""Idempotent database seeding with verified owner data only.

No fabricated experience, achievements, certificates, testimonials or analytics.
"""
from __future__ import annotations

from datetime import date

from flask import current_app

from app.extensions import db
from app.models import (
    AdminUser,
    AutomationWorkflow,
    Education,
    Profile,
    Project,
    ProjectCategory,
    ProjectMetric,
    ProjectTechnology,
    ResearchMetric,
    ResearchProject,
    Skill,
    SkillCategory,
    SystemSetting,
)
from app.models.base import utcnow


def seed_database() -> dict:
    created = {"admin": 0, "profile": 0, "education": 0, "skills": 0, "projects": 0, "research": 0}

    if AdminUser.query.count() == 0:
        admin = AdminUser(
            name=current_app.config["ADMIN_NAME"],
            email=current_app.config["ADMIN_EMAIL"].strip().lower(),
            role="admin",
            is_active=True,
        )
        admin.set_password(current_app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        created["admin"] = 1

    if Profile.query.count() == 0:
        db.session.add(_profile())
        created["profile"] = 1

    if Education.query.count() == 0:
        db.session.add_all(_education())
        created["education"] = 3

    if SkillCategory.query.count() == 0:
        categories, skills = _skills()
        db.session.add_all(categories)
        db.session.flush()
        db.session.add_all(skills)
        created["skills"] = len(categories)

    if ProjectCategory.query.count() == 0:
        db.session.add_all(_project_categories())

    if Project.query.count() == 0:
        projects = _projects()
        db.session.add_all(projects)
        created["projects"] = len(projects)

    if ResearchProject.query.count() == 0:
        db.session.add(_research())
        created["research"] = 1

    if AutomationWorkflow.query.count() == 0:
        db.session.add_all(_workflows())

    _seed_settings()

    db.session.commit()
    return created


def _profile() -> Profile:
    return Profile(
        full_name="Muwagamage Tharushi Prabhasha Dilshani",
        professional_title=(
            "AI/ML Engineer | Data Science Enthusiast | Python Developer | "
            "Generative AI Developer"
        ),
        summary=(
            "Final-year Information Technology undergraduate with hands-on experience in "
            "software application development, data analytics, AI-powered solutions, and "
            "workflow automation. Skilled in Python, SQL, Power BI, Microsoft Excel, REST APIs, "
            "and n8n, with practical experience developing database-driven applications, "
            "analyzing data, and implementing intelligent workflows. Interested in AI/ML, "
            "Data Science, and intelligent software development."
        ),
        about=(
            "Final-year BSc (Hons) Information Technology undergraduate at Horizon Campus, "
            "Malabe. Focused on AI/ML, data science, and intelligent software development, "
            "with project work spanning full-stack applications, computer vision, multi-agent "
            "AI systems, and workflow automation."
        ),
        career_goals=(
            "Interested in AI/ML, Data Science, and intelligent software development roles "
            "where data-driven and AI-powered solutions solve real problems."
        ),
        email="mtprabhashadilshani2001@gmail.com",
        phone="+94781582584",
        location="Kaduwela, Sri Lanka",
        linkedin_url="https://linkedin.com/in/prabhasha-dilshani-7258593a6",
        github_url="https://github.com/prabhasha-2001",
        github_username="prabhasha-2001",
        interests=[
            "Artificial Intelligence",
            "Machine Learning",
            "Data Science",
            "Generative AI",
            "Workflow Automation",
        ],
        languages=["Sinhala", "English"],
        is_active=True,
    )


def _education() -> list[Education]:
    return [
        Education(
            institution="Horizon Campus, Malabe",
            qualification="BSc (Hons) Information Technology",
            field_of_study="Information Technology",
            start_year="2023",
            end_year="2027",
            location="Malabe, Sri Lanka",
            description="Final-year undergraduate programme in Information Technology.",
            display_order=1,
            is_visible=True,
        ),
        Education(
            institution="Sabaragamuwa University of Sri Lanka",
            qualification="Certificate of English",
            start_year="2022",
            end_year="2022",
            location="Sri Lanka",
            display_order=2,
            is_visible=True,
        ),
        Education(
            institution="R/Sumana Balika Vidyalaya",
            qualification="G.C.E. Advanced Level – Physical Science",
            start_year="2021",
            end_year="2021",
            location="Sri Lanka",
            display_order=3,
            is_visible=True,
        ),
    ]


def _skills() -> tuple[list[SkillCategory], list[Skill]]:
    names = [
        "Programming Languages",
        "Data Science",
        "Machine Learning",
        "Artificial Intelligence",
        "Generative AI",
        "Backend Development",
        "Frontend Development",
        "Database Technologies",
        "Automation",
        "Developer Tools",
    ]
    categories = [
        SkillCategory(name=name, slug=_slug(name), display_order=index)
        for index, name in enumerate(names, start=1)
    ]
    by_name = {category.name: category for category in categories}
    verified = [
        ("Programming Languages", "Python", True),
        ("Programming Languages", "SQL", True),
        ("Data Science", "Power BI", True),
        ("Data Science", "Microsoft Excel", False),
        ("Backend Development", "REST APIs", True),
        ("Automation", "n8n", False),
    ]
    skills = [
        Skill(
            category=by_name[category],
            name=name,
            proficiency=None,
            is_featured=featured,
            is_visible=True,
            display_order=index,
        )
        for index, (category, name, featured) in enumerate(verified, start=1)
    ]
    return categories, skills


def _project_categories() -> list[ProjectCategory]:
    names = [
        "AI/ML Projects",
        "Data Science Projects",
        "Generative AI Projects",
        "Web Applications",
        "Backend Systems",
        "Automation Projects",
        "Academic Research",
    ]
    return [
        ProjectCategory(name=name, slug=_slug(name), display_order=index)
        for index, name in enumerate(names, start=1)
    ]


def _projects() -> list[Project]:
    categories = {category.name: category for category in ProjectCategory.query.all()}
    projects: list[Project] = []

    def make(**kwargs):
        technologies = kwargs.pop("technologies", [])
        metrics = kwargs.pop("metrics", [])
        project = Project(**kwargs, status="published", published_at=utcnow())
        project.technologies = [
            ProjectTechnology(name=technology, display_order=index)
            for index, technology in enumerate(technologies, start=1)
        ]
        project.metrics = [
            ProjectMetric(
                name=metric["name"],
                value=metric["value"],
                unit=metric.get("unit"),
                evaluation_run=metric.get("evaluation_run"),
                notes=metric.get("notes"),
            )
            for metric in metrics
        ]
        return project

    projects.append(
        make(
            title="AgriConnect – Smart Agriculture Microservices Platform",
            slug="agriconnect",
            short_description=(
                "Smart agriculture platform built on a microservices architecture with an API "
                "gateway, OAuth2/JWT security, and Dockerized services."
            ),
            description=(
                "A smart agriculture platform designed using a microservices-based architecture "
                "to support agriculture-related digital services. The system comprises multiple "
                "backend services behind a Spring Cloud Gateway, with centralized authentication "
                "and API documentation."
            ),
            architecture=(
                "Spring Cloud Gateway fronts multiple Spring Boot services backed by MySQL. "
                "Security uses OAuth2 with PKCE, JWT and API-key authentication. Services are "
                "documented with Swagger/OpenAPI and orchestrated with Docker Compose."
            ),
            solution=(
                "Service-oriented backend with a single gateway entry point, shared authentication "
                "concerns, and containerized development."
            ),
            github_url="https://github.com/prabhasha-2001",
            category=categories.get("Backend Systems"),
            project_type="Backend Systems",
            featured=True,
            display_order=1,
            technologies=[
                "Java", "Spring Boot", "MySQL", "Spring Cloud Gateway", "REST APIs",
                "OAuth2", "PKCE", "JWT", "API Key Authentication", "Swagger/OpenAPI",
                "React", "Docker Compose",
            ],
        )
    )

    projects.append(
        make(
            title="ChiliDoc AI – Multi-Agent Agronomic Advisor and Diagnostic System",
            slug="chilidoc-ai",
            short_description=(
                "AI-powered agricultural advisory application combining disease diagnosis, "
                "retrieval-augmented research, and agronomic response evaluation."
            ),
            description=(
                "An AI-powered agricultural advisory application combining disease diagnosis, "
                "retrieval-augmented research, and agronomic response evaluation."
            ),
            architecture=(
                "Three-agent workflow: (1) ReAct Diagnostic Agent, (2) RAG Researcher Agent, "
                "(3) Reflection Agronomy Critic Agent."
            ),
            implementation=(
                "LangGraph orchestrates the agents; LangChain and FAISS provide retrieval over "
                "agricultural PDFs with HuggingFace embeddings; Groq Llama 3.1 and OpenRouter "
                "provide model inference; Streamlit provides the interface."
            ),
            category=categories.get("Generative AI Projects"),
            project_type="Generative AI Projects",
            featured=True,
            display_order=2,
            technologies=[
                "Python", "Streamlit", "LangChain", "LangGraph", "FAISS",
                "HuggingFace Embeddings", "PyPDF", "Groq Llama 3.1", "OpenRouter",
            ],
        )
    )

    projects.append(
        make(
            title="Student Performance Analytics Dashboard",
            slug="student-performance-analytics",
            short_description=(
                "Interactive dashboard for exploring student performance data and generating "
                "AI/ML-supported insights."
            ),
            description=(
                "An interactive dashboard for exploring student performance data and generating "
                "AI/ML-supported insights."
            ),
            implementation=(
                "Built with Streamlit, Pandas and NumPy for data analysis, Plotly for interactive "
                "visualizations, and machine learning for predictive analysis."
            ),
            category=categories.get("Data Science Projects"),
            project_type="Data Science Projects",
            featured=True,
            display_order=3,
            technologies=[
                "Python", "Streamlit", "Pandas", "NumPy", "Plotly", "Machine Learning",
            ],
        )
    )

    projects.append(
        make(
            title="Vita Naturals – Cloud-Based Inventory Management System",
            slug="vita-naturals",
            short_description=(
                "Cloud-hosted inventory management system with authentication, MySQL storage, "
                "and interactive data visualizations."
            ),
            description=(
                "A cloud-based inventory management system providing inventory management, "
                "database integration, admin and user authentication, and data visualization."
            ),
            implementation=(
                "Python and Streamlit front end with a MySQL database hosted on Clever Cloud; "
                "Pandas and Plotly provide reporting and visualization."
            ),
            category=categories.get("Web Applications"),
            project_type="Web Applications",
            display_order=4,
            technologies=["Python", "Streamlit", "MySQL", "Clever Cloud", "Pandas", "Plotly"],
        )
    )

    projects.append(
        make(
            title="ChiliDoc – AI-Based Chili Leaf Disease Detection and Treatment Recommendation System",
            slug="chilidoc",
            short_description=(
                "Computer vision application classifying chili leaf conditions and supporting "
                "treatment recommendations."
            ),
            description=(
                "A computer vision application designed to classify chili leaf conditions and "
                "support treatment recommendations."
            ),
            dataset_info=(
                "1,852 images across six classes: Bacterial Spot, Cercospora Leaf Spot, Curl Virus, "
                "Healthy Leaf, Nutrition Deficiency, White Spot."
            ),
            implementation=(
                "TensorFlow and PyTorch models (CNN and Vision Transformer) served through Flask. "
                "Reported results below come from separate evaluation runs and must not be combined."
            ),
            category=categories.get("AI/ML Projects"),
            project_type="AI/ML Projects",
            featured=True,
            display_order=5,
            technologies=["Python", "TensorFlow", "PyTorch", "CNN", "Vision Transformer", "Flask"],
            metrics=[
                {
                    "name": "Accuracy",
                    "value": "99.38",
                    "unit": "%",
                    "evaluation_run": "Vision Transformer evaluation",
                    "notes": "Vision Transformer result as previously reported.",
                },
                {
                    "name": "Accuracy",
                    "value": "69.69",
                    "unit": "%",
                    "evaluation_run": "CNN training run (earlier)",
                    "notes": "Earlier CNN training run; not comparable to the later validation run.",
                },
                {
                    "name": "Accuracy",
                    "value": "74.06",
                    "unit": "%",
                    "evaluation_run": "CNN validation run (later)",
                    "notes": "Later CNN validation run; kept separate from the earlier run.",
                },
            ],
        )
    )

    projects.append(
        make(
            title="MoneySync – Personal Finance Tracker",
            slug="moneysync",
            short_description=(
                "Personal finance tracker with authenticated transaction management, financial "
                "summaries, and interactive charts."
            ),
            description=(
                "A personal finance tracker providing authentication, transaction management, "
                "financial summaries, and interactive charts."
            ),
            category=categories.get("Web Applications"),
            project_type="Web Applications",
            display_order=6,
            technologies=["Python", "Flask", "MySQL", "Chart.js"],
        )
    )

    return projects


def _research() -> ResearchProject:
    research = ResearchProject(
        title=(
            "Detecting Academic Stress Levels of University Students Using Digital Behavior "
            "and Machine Learning"
        ),
        slug="academic-stress-digital-behavior-ml",
        abstract=(
            "Academic research investigating whether digital behaviour can be used with machine "
            "learning to detect academic stress levels among university students. The study is "
            "based on 478 survey responses from 22 Sri Lankan universities/institutions, using "
            "PSS-10-based stress categories and Random Forest classification."
        ),
        methodology=(
            "PSS-10-based stress categorisation; Random Forest classification; cross-validation "
            "and held-out test evaluation, compared against a majority-class baseline."
        ),
        status="published",
        publication_status="Unpublished academic research",
        sample_size="478 survey responses",
        institutions_count="22 Sri Lankan universities/institutions",
        is_featured=True,
        notes=(
            "Random Forest cross-validation accuracy (75.4%) was lower than the majority-class "
            "baseline (82.7%) because the dataset is highly imbalanced (Moderate = 395 of 478, "
            "82.6%). Baseline and model metrics describe different evaluation approaches and must "
            "not be combined. The macro-F1 of 0.449 reflects weak minority-class performance. "
            "This research is not presented as published."
        ),
    )
    research.metrics = [
        ResearchMetric(
            name="Low stress",
            value="7",
            unit="responses (1.5%)",
            metric_type="distribution",
        ),
        ResearchMetric(
            name="Moderate stress",
            value="395",
            unit="responses (82.6%)",
            metric_type="distribution",
        ),
        ResearchMetric(
            name="High stress",
            value="76",
            unit="responses (15.9%)",
            metric_type="distribution",
        ),
        ResearchMetric(
            name="Random Forest cross-validation accuracy",
            value="75.4",
            unit="%",
            metric_type="model",
            notes="Model cross-validation accuracy.",
        ),
        ResearchMetric(
            name="Random Forest macro-F1",
            value="0.449",
            unit="",
            metric_type="model",
            notes="Macro-averaged F1 across classes.",
        ),
        ResearchMetric(
            name="Majority baseline cross-validation accuracy",
            value="82.7",
            unit="%",
            metric_type="baseline",
            notes="Majority-class baseline; higher than the model because of class imbalance.",
        ),
        ResearchMetric(
            name="Random Forest test accuracy",
            value="75.0",
            unit="%",
            metric_type="model",
            notes="Held-out test accuracy.",
        ),
    ]
    return research


def _workflows() -> list[AutomationWorkflow]:
    definitions = [
        ("Contact Message Notification", "contact.created", "Notify admin when a contact message is submitted."),
        ("Project Published Notification", "project.created", "Notify admin when a project is created."),
        ("Certificate Added Notification", "certificate.created", "Notify admin when a certificate is added."),
        ("Blog Published Notification", "blog.published", "Notify admin when a blog post is published."),
        ("Newsletter Welcome", "newsletter.subscribed", "Send a consent-based welcome email to a subscriber."),
        ("Weekly Analytics Report", "analytics.weekly", "Send the weekly analytics summary."),
        ("GitHub Update Notification", "github.updated", "Notify admin about repository updates."),
        ("Backup Completed Notification", "backup.completed", "Notify admin after a database backup."),
    ]
    return [
        AutomationWorkflow(
            name=name,
            slug=_slug(name),
            description=description,
            event_key=event_key,
            webhook_url=None,
            is_enabled=False,
        )
        for name, event_key, description in definitions
    ]


def _seed_settings() -> None:
    defaults = [
        ("site_name", "Prabhasha Nexus", "general", True),
        ("site_tagline", "AI-Powered Portfolio & Intelligence Management Platform", "general", True),
        ("owner_name", "Muwagamage Tharushi Prabhasha Dilshani", "general", True),
        ("contact_email", "mtprabhashadilshani2001@gmail.com", "general", True),
        ("show_ai_chat", True, "features", True),
        ("analytics_enabled", True, "analytics", False),
        ("maintenance_mode", False, "general", True),
        ("media_storage_backend", current_app.config.get("MEDIA_STORAGE_BACKEND", "local"), "media", False),
    ]
    for key, value, category, is_public in defaults:
        if SystemSetting.query.filter_by(key=key).first() is None:
            db.session.add(
                SystemSetting(key=key, value_json=value, category=category, is_public=is_public)
            )


def _slug(value: str) -> str:
    from app.utils.security import slugify

    return slugify(value)
