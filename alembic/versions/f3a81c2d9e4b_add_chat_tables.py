"""add_chat_tables

Revision ID: f3a81c2d9e4b
Revises: e91b82f43c10
Create Date: 2026-07-23 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a81c2d9e4b'
down_revision: Union[str, Sequence[str], None] = 'e91b82f43c10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_conv_participants_pair')
    )
    op.create_index(op.f('ix_conversation_participants_conversation_id'), 'conversation_participants', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_participants_user_id'), 'conversation_participants', ['user_id'], unique=False)

    op.create_table(
        'messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('sender_id', sa.Uuid(), nullable=False),
        sa.Column('client_msg_id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.String(length=4000), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_msg_id', name='uq_messages_client_msg_id')
    )
    op.create_index(op.f('ix_messages_client_msg_id'), 'messages', ['client_msg_id'], unique=True)
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index('ix_messages_conv_created', 'messages', ['conversation_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_messages_conv_created', table_name='messages')
    op.drop_index(op.f('ix_messages_sender_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_client_msg_id'), table_name='messages')
    op.drop_table('messages')

    op.drop_index(op.f('ix_conversation_participants_user_id'), table_name='conversation_participants')
    op.drop_index(op.f('ix_conversation_participants_conversation_id'), table_name='conversation_participants')
    op.drop_table('conversation_participants')

    op.drop_table('conversations')
