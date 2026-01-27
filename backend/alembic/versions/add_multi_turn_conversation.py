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

# revision identifiers, used by Alembic.
revision = 'add_multi_turn_conversation'
down_revision = '8a9b0c1d2e3f'  # Link to main branch
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration"""
    from sqlalchemy import text
    conn = op.get_bind()

    # 0. Create enums if not exist (PostgreSQL doesn't support IF NOT EXISTS for TYPE)
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE turnstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE sessiontype AS ENUM ('primary', 'retry', 'branch', 'background');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))

    # 1. Add new columns to conversations table (skip if exists)
    # Check and add each column individually
    columns_to_add = [
        ('turn_count', "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS turn_count INTEGER NOT NULL DEFAULT 0"),
        ('message_count', "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS message_count INTEGER NOT NULL DEFAULT 0"),
        ('shared_memory', "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS shared_memory JSON"),
        ('last_message_at', "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP"),
        ('current_session_id', "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS current_session_id VARCHAR(36) REFERENCES sessions(id) ON DELETE SET NULL"),
    ]
    for _, sql in columns_to_add:
        conn.execute(text(sql))

    # Create index if not exists
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversations_last_message_at ON conversations (last_message_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversations_current_session_id ON conversations (current_session_id)"))

    # 2. Create turns table if not exists
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS turns (
            id VARCHAR(36) PRIMARY KEY,
            conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            turn_number INTEGER NOT NULL,
            status turnstatus NOT NULL,
            user_message_id VARCHAR(26) NOT NULL REFERENCES messages(id),
            user_input VARCHAR(2000) NOT NULL,
            primary_session_id VARCHAR(26) REFERENCES sessions(id),
            skill_id VARCHAR(50),
            assistant_message_id VARCHAR(26) REFERENCES messages(id),
            assistant_response VARCHAR(5000),
            tokens_used INTEGER NOT NULL DEFAULT 0,
            duration_ms INTEGER,
            created_at TIMESTAMP NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_turns_conversation_id ON turns (conversation_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_turns_status ON turns (status)"))

    # 3. Add conversation_id
    conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(36)"))
    conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS turn_id VARCHAR(26)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_turn_id ON messages (turn_id)"))
    # Foreign keys - check if not exists
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE messages ADD CONSTRAINT fk_messages_conversation_id
                FOREIGN KEY (conversation_id) REFERENCES conversations(id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE messages ADD CONSTRAINT fk_messages_turn_id
                FOREIGN KEY (turn_id) REFERENCES turns(id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))

    # 4. Add conversation_id and turn_id to sessions table (using IF NOT EXISTS)
    conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(36)"))
    conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS turn_id VARCHAR(26)"))
    conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS session_type sessiontype DEFAULT 'primary'"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sessions_conversation_id ON sessions (conversation_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sessions_turn_id ON sessions (turn_id)"))
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE sessions ADD CONSTRAINT fk_sessions_conversation_id
                FOREIGN KEY (conversation_id) REFERENCES conversations(id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(text("""
        DO $$ BEGIN
            ALTER TABLE sessions ADD CONSTRAINT fk_sessions_turn_id
                FOREIGN KEY (turn_id) REFERENCES turns(id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))

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
