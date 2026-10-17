from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | None,
        actor: str,
        request_id: str,
        metadata: dict | None = None,
    ) -> AuditLog:
        item = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            request_id=request_id,
            metadata=metadata or {},
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
