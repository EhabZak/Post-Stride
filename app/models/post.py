from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime
from app.utils.timezone_helpers import format_utc_with_z


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    caption = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime)
    status = db.Column(db.String(50), nullable=False)  # draft|scheduled|publishing|published|partially_published|failed|canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='posts')
    post_platforms = db.relationship('PostPlatform', back_populates='post', cascade='all, delete-orphan')
    post_media = db.relationship('PostMedia', back_populates='post', cascade='all, delete-orphan')
      # 🔹 Add this relationship to scheduled_jobs
    scheduled_jobs = db.relationship(
        'ScheduledJob',
        back_populates='post',
        cascade='all, delete-orphan',  # removing from collection deletes child row
        passive_deletes=True,          # lets DB ON DELETE CASCADE handle parent delete
    )

    # Schema and Indexes
    schema_args = {'schema': SCHEMA} if environment == "production" else {}
    __table_args__ = (
        db.Index('idx_user_scheduled_time', 'user_id', 'scheduled_time'),
        db.Index('idx_status_scheduled_time', 'status', 'scheduled_time'),
        schema_args,  # dict must be the last element
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'caption': self.caption,
            'scheduled_time': format_utc_with_z(self.scheduled_time),
            'status': self.status,
            'created_at': format_utc_with_z(self.created_at),
            'updated_at': format_utc_with_z(self.updated_at)
        }
