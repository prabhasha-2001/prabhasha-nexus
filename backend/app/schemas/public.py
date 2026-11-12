"""Public-facing request schemas."""
from marshmallow import Schema, fields, validate


class ContactSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    email = fields.Email(required=True)
    phone = fields.Str(load_default=None, validate=validate.Length(max=50), allow_none=True)
    subject = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    message = fields.Str(required=True, validate=validate.Length(min=10, max=5000))
    website = fields.Str(load_default="", allow_none=True)  # honeypot


class NewsletterSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=150))
    consent = fields.Boolean(required=True)
    source = fields.Str(load_default="website", validate=validate.Length(max=100))


class AnalyticsEventSchema(Schema):
    event_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "page_view",
                "project_view",
                "certificate_view",
                "blog_view",
                "cv_download",
                "github_click",
                "contact_submit",
            ]
        ),
    )
    path = fields.Str(load_default="/", validate=validate.Length(max=500))
    page_type = fields.Str(load_default="page", validate=validate.Length(max=50))
    content_type = fields.Str(load_default=None, allow_none=True)
    content_id = fields.Int(load_default=None, allow_none=True)
    referrer = fields.Str(load_default=None, allow_none=True)
    device = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=30))
    source = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=120))
    visitor_id = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=64))


class ChatSchema(Schema):
    message = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    session_id = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=64))
