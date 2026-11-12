"""WSGI entry point for Gunicorn / production servers."""
from app import create_app

app = create_app()
