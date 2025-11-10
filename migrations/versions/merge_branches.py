"""Merge migration branches

Revision ID: merge_branches
Revises: add_gemini_api_key, deals_002
Create Date: 2025-11-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_branches'
down_revision = ('add_gemini_api_key', 'deals_002')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge commit, no changes needed
    pass


def downgrade():
    # This is a merge commit, no changes needed
    pass
