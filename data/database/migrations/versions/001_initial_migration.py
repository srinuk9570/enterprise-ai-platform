"""
Initial database migration.
Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('preferences', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
    )
    
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('model_parameters', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('tags', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_updated_at', 'conversations', ['updated_at'])
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('generation_time_ms', sa.Float(), nullable=True),
        sa.Column('finish_reason', sa.String(50), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'sequence_number', name='uq_conversation_sequence'),
    )
    
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    
    # Assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_type', sa.String(20), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('generation_params', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('generation_time_ms', sa.Float(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chart_configuration_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    op.create_index('idx_assets_user_id', 'assets', ['user_id'])
    op.create_index('idx_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('idx_assets_created_at', 'assets', ['created_at'])
    
    # Chart configurations table
    op.create_table(
        'chart_configurations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('chart_type', sa.String(20), nullable=False),
        sa.Column('data_source', sa.Text(), nullable=False),
        sa.Column('x_axis_column', sa.String(100), nullable=False),
        sa.Column('y_axis_columns', sa.Text(), nullable=False),
        sa.Column('group_by_column', sa.String(100), nullable=True),
        sa.Column('aggregation_function', sa.String(20), nullable=False, server_default='sum'),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('x_axis_label', sa.String(100), nullable=True),
        sa.Column('y_axis_label', sa.String(100), nullable=True),
        sa.Column('color_scheme', sa.String(50), server_default='default'),
        sa.Column('theme', sa.String(20), server_default='dark'),
        sa.Column('width', sa.Integer(), nullable=False, server_default='800'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='400'),
        sa.Column('show_legend', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_grid', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('show_tooltips', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('stacked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('normalized', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('cumulative', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('time_range_start', sa.DateTime(), nullable=True),
        sa.Column('time_range_end', sa.DateTime(), nullable=True),
        sa.Column('filters', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('limit_rows', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
    )
    
    op.create_index('idx_chart_configs_user_id', 'chart_configurations', ['user_id'])
    
    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('prefix', sa.String(10), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('audit_logs')
    op.drop_table('api_keys')
    op.drop_table('chart_configurations')
    op.drop_table('assets')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')