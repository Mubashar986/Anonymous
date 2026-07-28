"""create_user_permission_overrides_and_audit

Revision ID: b92d83f12011
Revises: 41bf5b20b59a
Create Date: 2026-07-27 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b92d83f12011'
down_revision: Union[str, Sequence[str], None] = '41bf5b20b59a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_permission_overrides',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('capability', sa.String(length=50), nullable=False),
        sa.Column('is_allowed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_permission_overrides_user_id', 'user_permission_overrides', ['user_id'], unique=False)
    op.create_index('uix_user_capability', 'user_permission_overrides', ['user_id', 'capability'], unique=True)

    op.create_table(
        'permission_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('target_id', sa.UUID(), nullable=False),
        sa.Column('capability', sa.String(length=50), nullable=False),
        sa.Column('previous_state', sa.String(length=20), nullable=True),
        sa.Column('new_state', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_permission_audit_logs_actor_id', 'permission_audit_logs', ['actor_id'], unique=False)
    op.create_index('ix_permission_audit_logs_target_id', 'permission_audit_logs', ['target_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_permission_audit_logs_target_id', table_name='permission_audit_logs')
    op.drop_index('ix_permission_audit_logs_actor_id', table_name='permission_audit_logs')
    op.drop_table('permission_audit_logs')

    op.drop_index('uix_user_capability', table_name='user_permission_overrides')
    op.drop_index('ix_user_permission_overrides_user_id', table_name='user_permission_overrides')
    op.drop_table('user_permission_overrides')
