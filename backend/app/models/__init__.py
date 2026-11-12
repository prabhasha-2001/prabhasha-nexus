"""ORM model registry."""
from app.models.ai import (
    AIConversation,
    AIGeneration,
    AIMessage,
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.models.analytics import AnalyticsEvent, PageView, Visitor
from app.models.automation import AutomationLog, AutomationWorkflow
from app.models.blog import BlogCategory, BlogPost, BlogTag, blog_post_tags
from app.models.certificate import Certificate, CertificateCategory
from app.models.communication import (
    ContactMessage,
    NewsletterSubscriber,
    Testimonial,
)
from app.models.media import MediaFile
from app.models.profile import (
    Achievement,
    Education,
    Experience,
    Profile,
    Skill,
    SkillCategory,
)
from app.models.project import (
    Project,
    ProjectCategory,
    ProjectImage,
    ProjectMetric,
    ProjectTechnology,
)
from app.models.research import ResearchMetric, ResearchProject
from app.models.resume import ResumeDownload, ResumeVersion
from app.models.system import (
    AdminActivityLog,
    Backup,
    Notification,
    ScheduledTask,
    SystemSetting,
)
from app.models.user import AdminUser, PasswordResetToken, RefreshToken

__all__ = [
    "AIConversation",
    "AIGeneration",
    "AIMessage",
    "AdminActivityLog",
    "AdminUser",
    "Achievement",
    "AnalyticsEvent",
    "AutomationLog",
    "AutomationWorkflow",
    "Backup",
    "BlogCategory",
    "BlogPost",
    "BlogTag",
    "blog_post_tags",
    "Certificate",
    "CertificateCategory",
    "ContactMessage",
    "Education",
    "Experience",
    "KnowledgeChunk",
    "KnowledgeDocument",
    "MediaFile",
    "NewsletterSubscriber",
    "Notification",
    "PageView",
    "PasswordResetToken",
    "Profile",
    "Project",
    "ProjectCategory",
    "ProjectImage",
    "ProjectMetric",
    "ProjectTechnology",
    "RefreshToken",
    "ResearchMetric",
    "ResearchProject",
    "ResumeDownload",
    "ResumeVersion",
    "ScheduledTask",
    "Skill",
    "SkillCategory",
    "SystemSetting",
    "Testimonial",
    "Visitor",
]
