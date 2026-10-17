from pathlib import Path


def test_sqlite_database_url_is_supported(monkeypatch, tmp_path):
    from sqlalchemy import create_engine

    db_path = Path(tmp_path) / "photobooking.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT 1").scalar() == 1
