"""rename pipeline_items confidence_score to confidence, alternatives_considered to alternatives

Revision ID: 478661dc4f2a
Revises: 92cc648701e0
Create Date: 2026-06-20 01:53:11.712200

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '478661dc4f2a'
down_revision: Union[str, Sequence[str], None] = '92cc648701e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('pipeline_items', 'confidence_score', new_column_name='confidence')
    op.alter_column('pipeline_items', 'alternatives_considered', new_column_name='alternatives')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('pipeline_items', 'confidence', new_column_name='confidence_score')
    op.alter_column('pipeline_items', 'alternatives', new_column_name='alternatives_considered')
