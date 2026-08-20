"""Initial EquityLens schema.

Revision ID: 20260819_0001
"""

from alembic import op

from app.db.models import Base

revision = "20260819_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
