"""StockPulse initial schema

Revision ID: 20260928_stockpulse_init
Revises:
Create Date: 2026-09-28 18:54:29.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260928_stockpulse_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=128), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('reorder_threshold', sa.Integer(), nullable=False),
        sa.Column('stock_level', sa.Integer(), nullable=False),
        sa.Column('demand_velocity', sa.Float(), nullable=False),
        sa.Column('category_average_demand', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)

    op.create_table(
        'pricing_suggestions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('trigger_reason', sa.String(length=64), nullable=False),
        sa.Column('suggested_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('rationale', sa.String(length=500), nullable=False),
        sa.Column('ai_reasoning', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pricing_suggestions_id'), 'pricing_suggestions', ['id'], unique=False)
    op.create_index(op.f('ix_pricing_suggestions_product_id'), 'pricing_suggestions', ['product_id'], unique=False)
    op.create_index(op.f('ix_pricing_suggestions_status'), 'pricing_suggestions', ['status'], unique=False)
    op.create_index(op.f('ix_pricing_suggestions_trigger_reason'), 'pricing_suggestions', ['trigger_reason'], unique=False)

    op.create_table(
        'reorder_suggestions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('trigger_reason', sa.String(length=64), nullable=False),
        sa.Column('suggested_quantity', sa.Integer(), nullable=False),
        sa.Column('rationale', sa.String(length=500), nullable=False),
        sa.Column('ai_reasoning', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reorder_suggestions_id'), 'reorder_suggestions', ['id'], unique=False)
    op.create_index(op.f('ix_reorder_suggestions_product_id'), 'reorder_suggestions', ['product_id'], unique=False)
    op.create_index(op.f('ix_reorder_suggestions_status'), 'reorder_suggestions', ['status'], unique=False)
    op.create_index(op.f('ix_reorder_suggestions_trigger_reason'), 'reorder_suggestions', ['trigger_reason'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reorder_suggestions_trigger_reason'), table_name='reorder_suggestions')
    op.drop_index(op.f('ix_reorder_suggestions_status'), table_name='reorder_suggestions')
    op.drop_index(op.f('ix_reorder_suggestions_product_id'), table_name='reorder_suggestions')
    op.drop_index(op.f('ix_reorder_suggestions_id'), table_name='reorder_suggestions')
    op.drop_table('reorder_suggestions')

    op.drop_index(op.f('ix_pricing_suggestions_trigger_reason'), table_name='pricing_suggestions')
    op.drop_index(op.f('ix_pricing_suggestions_status'), table_name='pricing_suggestions')
    op.drop_index(op.f('ix_pricing_suggestions_product_id'), table_name='pricing_suggestions')
    op.drop_index(op.f('ix_pricing_suggestions_id'), table_name='pricing_suggestions')
    op.drop_table('pricing_suggestions')

    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_table('products')
