import logging

from sqlalchemy.orm import Session

from app.core.logging import request_id_ctx
from app.repositories.audit import AuditRepository

logger = logging.getLogger(__name__)


def record_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    actor: str,
    metadata: dict | None = None,
) -> None:
    try:
        AuditRepository(db).record(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            request_id=request_id_ctx.get(),
            metadata=metadata,
        )
    except Exception:
        # Audit must not turn a successful business operation into a failure.
        db.rollback()
        logger.exception("audit_record_failed action=%s entity_type=%s entity_id=%s", action, entity_type, entity_id)
