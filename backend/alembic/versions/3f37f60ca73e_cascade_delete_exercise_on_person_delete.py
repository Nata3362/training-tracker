"""cascade delete exercise on person delete

Revision ID: 3f37f60ca73e
Revises: 0a29ac6cf2df
Create Date: 2026-09-20 18:12:23.555663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f37f60ca73e'
down_revision: Union[str, Sequence[str], None] = '0a29ac6cf2df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('exercise_person_id_fkey'), 'exercise', type_='foreignkey')
    op.create_foreign_key(
        op.f('exercise_person_id_fkey'), 'exercise', 'people', ['person_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('exercise_person_id_fkey'), 'exercise', type_='foreignkey')
    op.create_foreign_key(op.f('exercise_person_id_fkey'), 'exercise', 'people', ['person_id'], ['id'])
