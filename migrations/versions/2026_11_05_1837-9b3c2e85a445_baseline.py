"""baseline

Revision ID: 9b3c2e85a445
Revises: baf583739a2e
Create Date: 2026-11-05 18:37:48.841859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b3c2e85a445'
down_revision: Union[str, Sequence[str], None] = 'baf583739a2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
