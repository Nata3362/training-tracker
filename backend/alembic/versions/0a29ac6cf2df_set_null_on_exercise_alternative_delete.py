"""set null on exercise alternative delete

Revision ID: 0a29ac6cf2df
Revises: e12fc75b628a
Create Date: 2026-09-20 18:02:23.400400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a29ac6cf2df'
down_revision: Union[str, Sequence[str], None] = 'e12fc75b628a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('exercise_alternative2_fkey'), 'exercise', type_='foreignkey')
    op.drop_constraint(op.f('exercise_alternative1_fkey'), 'exercise', type_='foreignkey')
    op.create_foreign_key(
        op.f('exercise_alternative1_fkey'), 'exercise', 'exercise', ['alternative1'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        op.f('exercise_alternative2_fkey'), 'exercise', 'exercise', ['alternative2'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('exercise_alternative1_fkey'), 'exercise', type_='foreignkey')
    op.drop_constraint(op.f('exercise_alternative2_fkey'), 'exercise', type_='foreignkey')
    op.create_foreign_key(op.f('exercise_alternative1_fkey'), 'exercise', 'exercise', ['alternative1'], ['id'])
    op.create_foreign_key(op.f('exercise_alternative2_fkey'), 'exercise', 'exercise', ['alternative2'], ['id'])
