"""
URL patterns for the auth app.

All routes live under /api/v1/auth/ (prefixed in config/urls.py).
"""
from django.urls import path
from .views import LoginView, MeView, RefreshView, RegisterView

urlpatterns = [
    path("register", RegisterView.as_view(), name="auth-register"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="auth-me"),
]
