from alembic import op
import sqlalchemy as sa

revision = "0003_booking_lifecycle"
down_revision = "0002_create_bookings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bookings", sa.Column("idempotency_key", sa.String(100), nullable=True))
    # Existing rows get deterministic unique keys before the NOT NULL constraint.
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM bookings WHERE idempotency_key IS NULL")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE bookings SET idempotency_key = :key WHERE id = :id"),
            {"key": f"legacy-{row.id}", "id": row.id},
        )
    op.alter_column("bookings", "idempotency_key", nullable=False)
    op.create_unique_constraint("uq_bookings_idempotency_key", "bookings", ["idempotency_key"])


def downgrade():
    op.drop_constraint("uq_bookings_idempotency_key", "bookings", type_="unique")
    op.drop_column("bookings", "idempotency_key")
