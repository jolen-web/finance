"""Add default_page column to dashboard_preferences table

Revision ID: add_default_page_col
Revises: ef0c540e4055
Create Date: 2025-11-01 08:22:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_default_page_col'
down_revision = 'ef0c540e4055'
branch_labels = None
depends_on = None


def upgrade():
    # Add the default_page column to dashboard_preferences table
    op.add_column('dashboard_preferences',
                  sa.Column('default_page', sa.String(length=50), nullable=True, server_default='dashboard'))
    # Update existing rows to have the default value
    op.execute("UPDATE dashboard_preferences SET default_page = 'dashboard' WHERE default_page IS NULL")
    # Make column not nullable after setting defaults
    op.alter_column('dashboard_preferences', 'default_page', nullable=False)


def downgrade():
    op.drop_column('dashboard_preferences', 'default_page')
