"""Add multi-provider authentication support to users table

Revision ID: 6f9h3j4k5l6m
Revises: 5e8f2g6i7j8k
Create Date: 2026-01-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f9h3j4k5l6m'
down_revision: Union[str, Sequence[str], None] = '6e9g4j5k6l7m'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Add new columns to users table
    op.add_column('users', sa.Column('display_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(length=50), nullable=False, server_default='email_password'))
    
    # WeChat OAuth columns
    op.add_column('users', sa.Column('wechat_openid', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('wechat_unionid', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('wechat_nickname', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('wechat_headimgurl', sa.String(length=500), nullable=True))
    
    # Create indexes for WeChat columns
    op.create_index(op.f('ix_users_wechat_openid'), 'users', ['wechat_openid'], unique=True)
    
    # Gmail OAuth columns
    op.add_column('users', sa.Column('gmail_sub', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('gmail_email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('gmail_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('gmail_picture', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('gmail_access_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('gmail_refresh_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('gmail_token_expires_at', sa.DateTime(), nullable=True))
    
    # Create indexes for Gmail columns
    op.create_index(op.f('ix_users_gmail_sub'), 'users', ['gmail_sub'], unique=True)
    
    # Add email_verified column
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    # Make password_hash nullable (for OAuth users)
    op.alter_column('users', 'password_hash', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Remove email_verified column
    op.drop_column('users', 'email_verified')
    
    # Remove Gmail OAuth columns and indexes
    op.drop_index(op.f('ix_users_gmail_sub'), table_name='users')
    op.drop_column('users', 'gmail_token_expires_at')
    op.drop_column('users', 'gmail_refresh_token')
    op.drop_column('users', 'gmail_access_token')
    op.drop_column('users', 'gmail_picture')
    op.drop_column('users', 'gmail_name')
    op.drop_column('users', 'gmail_email')
    op.drop_column('users', 'gmail_sub')
    
    # Remove WeChat OAuth columns and indexes
    op.drop_index(op.f('ix_users_wechat_openid'), table_name='users')
    op.drop_column('users', 'wechat_headimgurl')
    op.drop_column('users', 'wechat_nickname')
    op.drop_column('users', 'wechat_unionid')
    op.drop_column('users', 'wechat_openid')
    
    # Remove auth_provider, display_name, avatar_url columns
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'display_name')
    
    # Make password_hash not nullable again
    op.alter_column('users', 'password_hash', nullable=False)
