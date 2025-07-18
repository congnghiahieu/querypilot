"""Initial migration

Revision ID: 8cb25d17ad0c
Revises: 
Create Date: 2025-07-13 11:48:45.260748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '8cb25d17ad0c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('cognito_user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_cognito_user_id'), 'users', ['cognito_user_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('chat_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)
    op.create_table('knowledge_bases',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('filename', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('original_filename', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('file_path', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
    sa.Column('file_type', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('upload_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processing_status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_bases_user_id'), 'knowledge_bases', ['user_id'], unique=False)
    op.create_table('user_settings',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('vai_tro', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('chi_nhanh', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('pham_vi', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('du_lieu', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('datasource_permissions', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chat_messages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('chat_session_id', sa.Uuid(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('sql_query', sa.Text(), nullable=True),
    sa.Column('response_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('execution_time', sa.Float(), nullable=True),
    sa.Column('rows_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_chat_session_id'), 'chat_messages', ['chat_session_id'], unique=False)
    op.create_table('knowledge_base_insights',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('knowledge_base_id', sa.Uuid(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('key_insights', sa.Text(), nullable=True),
    sa.Column('entities', sa.Text(), nullable=True),
    sa.Column('topics', sa.Text(), nullable=True),
    sa.Column('processed_content', sa.Text(), nullable=True),
    sa.Column('processing_time', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_base_insights_knowledge_base_id'), 'knowledge_base_insights', ['knowledge_base_id'], unique=True)
    op.create_table('chat_data_results',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('message_id', sa.Uuid(), nullable=False),
    sa.Column('data_json', sa.Text(), nullable=True),
    sa.Column('columns', sa.Text(), nullable=True),
    sa.Column('shape_rows', sa.Integer(), nullable=False),
    sa.Column('shape_cols', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_data_results_message_id'), 'chat_data_results', ['message_id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_chat_data_results_message_id'), table_name='chat_data_results')
    op.drop_table('chat_data_results')
    op.drop_index(op.f('ix_knowledge_base_insights_knowledge_base_id'), table_name='knowledge_base_insights')
    op.drop_table('knowledge_base_insights')
    op.drop_index(op.f('ix_chat_messages_chat_session_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_knowledge_bases_user_id'), table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_cognito_user_id'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
