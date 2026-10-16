from alembic import op
import sqlalchemy as sa
revision="0001_create_catalog"
down_revision=None
branch_labels=None
depends_on=None


def upgrade():
    op.create_table("photography_sessions",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("slug", sa.String(80), nullable=False),
                    sa.Column("name", sa.String(120), nullable=False),
                    sa.Column("description", sa.Text(), nullable=False),
                    sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true())
                    )
    op.create_index("ix_photography_sessions_slug","photography_sessions",["slug"],unique=True)

    op.create_table("session_packages",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("session_id", sa.Integer(), nullable=False),
                    sa.Column("name", sa.String(120), nullable=False),
                    sa.Column("description", sa.Text(), nullable=False),
                    sa.Column("price", sa.Numeric(10, 2), nullable=False),
                    sa.Column("duration_minutes", sa.Integer(), nullable=False),
                    sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
                    sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
                    sa.ForeignKeyConstraint(["session_id"], ["photography_sessions.id"], ondelete="CASCADE")
                    )
    op.create_index("ix_session_packages_session_id", "session_packages", ["session_id"])


def downgrade():
    op.drop_index("ix_session_packages_session_id", table_name="session_packages")
    op.drop_table("session_packages")
    op.drop_index("ix_photography_sessions_slug", table_name="photography_sessions")
    op.drop_table("photography_sessions")
