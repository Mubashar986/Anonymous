"""add_blogs_table

Revision ID: c91a74d2b910
Revises: 8616736ea14f
Create Date: 2026-07-20 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91a74d2b910'
down_revision: Union[str, Sequence[str], None] = '8616736ea14f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'blogs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='blog_status', native_enum=False), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blogs_author_id'), 'blogs', ['author_id'], unique=False)
    op.create_index(op.f('ix_blogs_status'), 'blogs', ['status'], unique=False)
    op.create_index(op.f('ix_blogs_title'), 'blogs', ['title'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_blogs_title'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_status'), table_name='blogs')
    op.drop_index(op.f('ix_blogs_author_id'), table_name='blogs')
    op.drop_table('blogs')
