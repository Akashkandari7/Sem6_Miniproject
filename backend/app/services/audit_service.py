"""
Audit logging service.

Usage::

    from app.services.audit_service import log_action

    # After a successful DB commit in a route:
    log_action('question.create', resource_type='question', resource_id=q.id)

    # For a failure (e.g. failed login) — user_id may be unknown:
    log_action('auth.login', status='failure', details={'email': email})

``log_action`` never raises — audit failures must not disrupt the request.
"""

from datetime import datetime, timezone


def log_action(
    action: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    details: dict | None = None,
    status: str = 'success',
    user_id: int | None = None,
) -> None:
    """
    Persist one audit log entry.

    Parameters
    ----------
    action        : dot-separated event name, e.g. ``'question.create'``
    resource_type : the affected model, e.g. ``'question'``, ``'paper'``
    resource_id   : primary key of the affected record, if applicable
    details       : free-form dict for extra context (subject, topic, etc.)
    status        : ``'success'`` (default) or ``'failure'``
    user_id       : explicit user id; auto-detected from ``g._rbac_user`` when omitted
    """
    try:
        from flask import g, request, has_request_context
        from app.extensions import db
        from app.models.audit_log import AuditLog

        if user_id is None and has_request_context():
            rbac_user = getattr(g, '_rbac_user', None)
            if rbac_user:
                user_id = rbac_user.id

        ip_address = request.remote_addr if has_request_context() else None

        entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            status=status,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        # Audit logging must never crash the calling request.
        pass
