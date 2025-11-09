"""Add deals table for credit card promotions

Revision ID: deals_001
Revises:
Create Date: 2025-11-09 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'deals_001'
down_revision = 'enhance_regex_patterns'
branch_labels = None
depends_on = None


def upgrade():
    # Create deals table
    op.create_table(
        'deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('card_issuer', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('merchant', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('card_type', sa.String(100), nullable=True),
        sa.Column('discount_type', sa.String(50), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('reward_points', sa.Integer(), nullable=True),
        sa.Column('cashback_percent', sa.Float(), nullable=True),
        sa.Column('promotion_start_date', sa.String(50), nullable=True),
        sa.Column('promotion_end_date', sa.String(50), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('promotion_details', sa.Text(), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('ix_deals_source', 'deals', ['source'])
    op.create_index('ix_deals_category', 'deals', ['category'])
    op.create_index('ix_deals_merchant', 'deals', ['merchant'])
    op.create_index('ix_deals_card_issuer', 'deals', ['card_issuer'])
    op.create_index('ix_deals_is_active', 'deals', ['is_active'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_deals_is_active', table_name='deals')
    op.drop_index('ix_deals_card_issuer', table_name='deals')
    op.drop_index('ix_deals_merchant', table_name='deals')
    op.drop_index('ix_deals_category', table_name='deals')
    op.drop_index('ix_deals_source', table_name='deals')

    # Drop table
    op.drop_table('deals')
