"""add_comments_table

Revision ID: d18e952f4a12
Revises: c91a74d2b910
Create Date: 2026-07-20 13:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd18e952f4a12'
down_revision: Union[str, Sequence[str], None] = 'c91a74d2b910'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'comments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('blog_id', sa.Uuid(), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_author_id'), 'comments', ['author_id'], unique=False)
    op.create_index(op.f('ix_comments_blog_id'), 'comments', ['blog_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_comments_blog_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_author_id'), table_name='comments')
    op.drop_table('comments')
