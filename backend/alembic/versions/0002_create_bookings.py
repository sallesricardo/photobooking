from alembic import op
import sqlalchemy as sa

revision = "0002_create_bookings"
down_revision = "0001_create_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_event_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="confirmed"),
        sa.Column("customer_name", sa.String(160), nullable=True),
        sa.Column("customer_phone", sa.String(40), nullable=True),
        sa.Column("whatsapp_url", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["photography_sessions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["package_id"], ["session_packages.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("provider_event_id"),
    )
    op.create_index("ix_bookings_session_id", "bookings", ["session_id"])
    op.create_index("ix_bookings_package_id", "bookings", ["package_id"])
    op.create_index("ix_bookings_start_at", "bookings", ["start_at"])


def downgrade():
    op.drop_index("ix_bookings_start_at", table_name="bookings")
    op.drop_index("ix_bookings_package_id", table_name="bookings")
    op.drop_index("ix_bookings_session_id", table_name="bookings")
    op.drop_table("bookings")
