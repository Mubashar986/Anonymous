"""add_follows_table

Revision ID: e91b82f43c10
Revises: 73cb0b7bb88b
Create Date: 2026-07-23 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e91b82f43c10'
down_revision: Union[str, Sequence[str], None] = '73cb0b7bb88b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'follows',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('follower_id', sa.Uuid(), nullable=False),
        sa.Column('target_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('follower_id != target_id', name='ck_follows_no_self_follow'),
        sa.UniqueConstraint('follower_id', 'target_id', name='uq_follows_follower_target')
    )
    op.create_index(op.f('ix_follows_follower_id'), 'follows', ['follower_id'], unique=False)
    op.create_index(op.f('ix_follows_target_id'), 'follows', ['target_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_follows_target_id'), table_name='follows')
    op.drop_index(op.f('ix_follows_follower_id'), table_name='follows')
    op.drop_table('follows')
