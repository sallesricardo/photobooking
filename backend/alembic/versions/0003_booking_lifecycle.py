from alembic import op
import sqlalchemy as sa

revision = "0003_booking_lifecycle"
down_revision = "0002_create_bookings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bookings", sa.Column("idempotency_key", sa.String(100), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM bookings WHERE idempotency_key IS NULL")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE bookings SET idempotency_key = :key WHERE id = :id"),
            {"key": f"legacy-{row.id}", "id": row.id},
        )

    # SQLite does not support ALTER COLUMN / ADD CONSTRAINT directly.
    # Batch mode lets Alembic recreate the table when necessary while
    # remaining compatible with PostgreSQL.
    with op.batch_alter_table("bookings", recreate="auto") as batch_op:
        batch_op.alter_column("idempotency_key", nullable=False)
        batch_op.create_unique_constraint(
            "uq_bookings_idempotency_key", ["idempotency_key"]
        )


def downgrade():
    with op.batch_alter_table("bookings", recreate="auto") as batch_op:
        batch_op.drop_constraint("uq_bookings_idempotency_key", type_="unique")
        batch_op.drop_column("idempotency_key")
