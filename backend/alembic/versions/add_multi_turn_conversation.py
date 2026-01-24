"""
Database Migration: Add multi-turn conversation support

Revision ID: add_multi_turn_conversation
Revises: previous_migration
Create Date: 2024-01-24

This migration adds support for multi-turn conversations:
1. Add turn_count, message_count to conversations
2. Add shared_memory (JSON) to conversations
3. Add last_message_at to conversations
4. Create turns table
5. Add conversation_id, turn_id to messages
6. Add conversation_id, turn_id to sessions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_multi_turn_conversation'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration"""

    # 1. Add new columns to conversations table
    op.add_column('conversations', sa.Column('turn_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('conversations', sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('conversations', sa.Column('shared_memory', sa.JSON(), nullable=True))
    op.add_column('conversations', sa.Column('last_message_at', sa.DateTime(), nullable=True))
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'])

    # 2. Create turns table
    op.create_table(
        'turns',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='turnstatus'), nullable=False),
        sa.Column('user_message_id', sa.String(length=26), nullable=False),
        sa.Column('user_input', sa.String(length=2000), nullable=False),
        sa.Column('primary_session_id', sa.String(length=26), nullable=True),
        sa.Column('skill_id', sa.String(length=50), nullable=True),
        sa.Column('assistant_message_id', sa.String(length=26), nullable=True),
        sa.Column('assistant_response', sa.String(length=5000), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['assistant_message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['primary_session_id'], ['sessions.id']),
    )
    op.create_index('ix_turns_conversation_id', 'turns', ['conversation_id'])
    op.create_index('ix_turns_status', 'turns', ['status'])

    # 3. Add conversation_id and turn_id to messages table
    op.add_column('messages', sa.Column('conversation_id', sa.String(length=36), nullable=True))
    op.add_column('messages', sa.Column('turn_id', sa.String(length=26), nullable=True))
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_turn_id', 'messages', ['turn_id'])
    op.create_foreign_key('fk_messages_conversation_id', 'messages', 'conversations', ['conversation_id'], ['id'])
    op.create_foreign_key('fk_messages_turn_id', 'messages', 'turns', ['turn_id'], ['id'])

    # 4. Add conversation_id and turn_id to sessions table
    op.add_column('sessions', sa.Column('conversation_id', sa.String(length=36), nullable=True))
    op.add_column('sessions', sa.Column('turn_id', sa.String(length=26), nullable=True))
    op.add_column('sessions', sa.Column('session_type', sa.Enum('primary', 'retry', 'branch', 'background', name='sessiontype'), nullable=True, server_default='primary'))
    op.create_index('ix_sessions_conversation_id', 'sessions', ['conversation_id'])
    op.create_index('ix_sessions_turn_id', 'sessions', ['turn_id'])
    op.create_foreign_key('fk_sessions_conversation_id', 'sessions', 'conversations', ['conversation_id'], ['id'])
    op.create_foreign_key('fk_sessions_turn_id', 'sessions', 'turns', ['turn_id'], ['id'])

    # 5. Migrate existing data
    # For existing conversations, set turn_count and message_count based on existing messages
    op.execute("""
        UPDATE conversations c
        SET message_count = (
            SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id
        ),
        last_message_at = (
            SELECT MAX(created_at) FROM messages m WHERE m.conversation_id = c.id
        )
    """)

    print("✅ Multi-turn conversation migration completed")


def downgrade():
    """Revert migration"""

    # Remove foreign keys first
    op.drop_constraint('fk_sessions_turn_id', 'sessions', type_='foreignkey')
    op.drop_constraint('fk_sessions_conversation_id', 'sessions', type_='foreignkey')
    op.drop_constraint('fk_messages_turn_id', 'messages', type_='foreignkey')
    op.drop_constraint('fk_messages_conversation_id', 'messages', type_='foreignkey')

    # Remove indexes
    op.drop_index('ix_sessions_turn_id', 'sessions')
    op.drop_index('ix_sessions_conversation_id', 'sessions')
    op.drop_index('ix_messages_turn_id', 'messages')
    op.drop_index('ix_messages_conversation_id', 'messages')
    op.drop_index('ix_turns_status', 'turns')
    op.drop_index('ix_turns_conversation_id', 'turns')
    op.drop_index('ix_conversations_last_message_at', 'conversations')

    # Remove columns
    op.drop_column('sessions', 'session_type')
    op.drop_column('sessions', 'turn_id')
    op.drop_column('sessions', 'conversation_id')
    op.drop_column('messages', 'turn_id')
    op.drop_column('messages', 'conversation_id')
    op.drop_column('conversations', 'last_message_at')
    op.drop_column('conversations', 'shared_memory')
    op.drop_column('conversations', 'message_count')
    op.drop_column('conversations', 'turn_count')

    # Drop turns table
    op.drop_table('turns')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS turnstatus')
    op.execute('DROP TYPE IF EXISTS sessiontype')

    print("✅ Multi-turn conversation migration reverted")
