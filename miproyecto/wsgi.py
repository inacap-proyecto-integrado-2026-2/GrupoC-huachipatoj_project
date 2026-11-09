"""
WSGI config for miproyecto project.

It exposes the WSGI callable as a module-level variable named ``application``
and ``app`` (for Vercel serverless runtime).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miproyecto.settings')

application = get_wsgi_application()
app = application
