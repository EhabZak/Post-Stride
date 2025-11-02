from app.models import db
from datetime import datetime
import os
from app.utils.timezone_helpers import format_utc_with_z

# Get environment and schema for production
environment = os.getenv('FLASK_ENV', 'development')
SCHEMA = os.getenv('SCHEMA', 'flask_schema')

class ScheduledJob(db.Model):
    __tablename__ = 'scheduled_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('social_platforms.id'), nullable=True)
    job_type = db.Column(db.String(32), nullable=False)
    queue_name = db.Column(db.String(64), nullable=False)
    rq_job_id = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(32), nullable=False)
    scheduled_for = db.Column(db.DateTime, nullable=False)
    enqueued_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    canceled_at = db.Column(db.DateTime, nullable=True)
    attempts = db.Column(db.Integer, nullable=False, server_default='0')
    max_retries = db.Column(db.Integer, nullable=False, server_default='0')
    error_message = db.Column(db.Text, nullable=True)
    traceback = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # Relationships
    post = db.relationship('Post', backref='scheduled_jobs')
    platform = db.relationship('SocialPlatform', backref='scheduled_jobs')
    post = db.relationship('Post', back_populates='scheduled_jobs')
    
    # Table args for production schema
    schema_args = {'schema': SCHEMA} if environment == "production" else {}
    __table_args__ = (
        db.Index('idx_scheduled_jobs_status_when', 'status', 'scheduled_for'),
        schema_args,  # dict must be the last element
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'platform_id': self.platform_id,
            'job_type': self.job_type,
            'queue_name': self.queue_name,
            'rq_job_id': self.rq_job_id,
            'status': self.status,
            'scheduled_for': format_utc_with_z(self.scheduled_for),
            'enqueued_at': format_utc_with_z(self.enqueued_at),
            'started_at': format_utc_with_z(self.started_at),
            'finished_at': format_utc_with_z(self.finished_at),
            'canceled_at': format_utc_with_z(self.canceled_at),
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'traceback': self.traceback,
            'created_by_user_id': self.created_by_user_id,
            'created_at': format_utc_with_z(self.created_at),
            'updated_at': format_utc_with_z(self.updated_at),
        }
