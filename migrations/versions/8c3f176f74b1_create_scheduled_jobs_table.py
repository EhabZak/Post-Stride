"""Create scheduled_jobs table

Revision ID: 8c3f176f74b1
Revises: 5ff348b4b0b9
Create Date: 2025-09-30 23:21:30.298673

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c3f176f74b1'
down_revision = '5ff348b4b0b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform_id', sa.Integer(), sa.ForeignKey('social_platforms.id'), nullable=True),
        sa.Column('job_type', sa.String(length=32), nullable=False),
        sa.Column('queue_name', sa.String(length=64), nullable=False),
        sa.Column('rq_job_id', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('enqueued_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_scheduled_jobs_status_when', 'scheduled_jobs', ['status', 'scheduled_for'])


def downgrade():
    op.drop_index('idx_scheduled_jobs_status_when', table_name='scheduled_jobs')
    op.drop_table('scheduled_jobs')
