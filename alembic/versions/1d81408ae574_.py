"""empty message

Revision ID: 1d81408ae574
Revises: a25e52dbd0bc
Create Date: 2026-05-04 08:12:38.084889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d81408ae574'
down_revision: Union[str, Sequence[str], None] = 'a25e52dbd0bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
