"""
Audit logging helper.

Every significant user action (upload, delete, register, login) calls
log_action() which writes one row to the AuditLog table.  The table lets
admins reconstruct what happened to a file if something goes wrong.
"""
from .models import AuditLog


def _get_client_ip(request) -> str | None:
    """
    Extract the real client IP from the request.

    When the API sits behind a reverse proxy (Nginx / load balancer), the
    true client address is forwarded in X-Forwarded-For.  We read that first
    and fall back to REMOTE_ADDR for direct connections.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        # The header may contain a comma-separated list of IPs; the
        # leftmost entry is the original client.
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(request, action: str, *, details: dict | None = None, job=None) -> None:
    """
    Write one AuditLog row.

    Parameters
    ----------
    request : HttpRequest
        The current Django request — used to read the authenticated user
        and the client IP address.
    action : str
        One of AuditLog.ACTION_* constants  (upload / delete / login / register).
    details : dict, optional
        Extra context stored as JSON (e.g. filename, file_size_bytes).
    job : ResumeParseJob, optional
        If the action is related to a specific parse job, pass it here so
        the audit row is linked to that job in the database.
    """
    user = request.user if request.user.is_authenticated else None
    AuditLog.objects.create(
        user=user,
        job=job,
        action=action,
        details=details or {},
        ip_address=_get_client_ip(request),
    )
