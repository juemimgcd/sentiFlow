"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


# 应用模板生成的数据库结构升级。
def upgrade() -> None:
    """Upgrade schema."""
    ${upgrades if upgrades else "pass"}


# 回滚模板生成的数据库结构升级。
def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
