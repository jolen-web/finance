"""Add image and detailed description fields to deals table

Revision ID: deals_002
Revises: deals_001
Create Date: 2025-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'deals_002'
down_revision = 'deals_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to deals table
    op.add_column('deals', sa.Column('detailed_description', sa.Text(), nullable=True))
    op.add_column('deals', sa.Column('image_url', sa.String(500), nullable=True))
    op.add_column('deals', sa.Column('merchant_logo_url', sa.String(500), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('deals', 'merchant_logo_url')
    op.drop_column('deals', 'image_url')
    op.drop_column('deals', 'detailed_description')
