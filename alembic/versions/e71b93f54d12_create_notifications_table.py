"""create_notifications_table

Revision ID: e71b93f54d12
Revises: b92d83f12011
Create Date: 2026-07-27 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e71b93f54d12'
down_revision = 'b92d83f12011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uix_notifications_idempotency')
    )
    op.create_index('idx_notifications_recipient_created', 'notifications', ['recipient_id', 'created_at'], unique=False)
    op.create_index('idx_notifications_recipient_unread', 'notifications', ['recipient_id', 'is_read'], unique=False)
    op.create_index(op.f('ix_notifications_actor_id'), 'notifications', ['actor_id'], unique=False)
    op.create_index(op.f('ix_notifications_event_type'), 'notifications', ['event_type'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_recipient_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_event_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_actor_id'), table_name='notifications')
    op.drop_index('idx_notifications_recipient_unread', table_name='notifications')
    op.drop_index('idx_notifications_recipient_created', table_name='notifications')
    op.drop_table('notifications')
