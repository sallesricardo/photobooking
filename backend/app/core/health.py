from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import engine


def check_database() -> bool:
    with Session(engine) as db:
        db.execute(text("SELECT 1"))
    return True
