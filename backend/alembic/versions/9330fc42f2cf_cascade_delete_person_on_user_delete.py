"""cascade delete person on user delete

Revision ID: 9330fc42f2cf
Revises: 3f37f60ca73e
Create Date: 2026-09-21 21:14:14.669985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9330fc42f2cf'
down_revision: Union[str, Sequence[str], None] = '3f37f60ca73e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('people_user_id_fkey'), 'people', type_='foreignkey')
    op.create_foreign_key(
        op.f('people_user_id_fkey'), 'people', 'users', ['user_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('people_user_id_fkey'), 'people', type_='foreignkey')
    op.create_foreign_key(op.f('people_user_id_fkey'), 'people', 'users', ['user_id'], ['id'])
