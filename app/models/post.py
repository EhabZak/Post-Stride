from .db import db, environment, SCHEMA, add_prefix_for_prod
import uuid
from datetime import datetime


class Post(db.Model):
    __tablename__ = 'posts'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    caption = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime)
    status = db.Column(db.String(50), nullable=False)  # draft|scheduled|publishing|published|partially_published|failed|canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='posts')
    post_platforms = db.relationship('PostPlatform', back_populates='post', cascade='all, delete-orphan')
    post_media = db.relationship('PostMedia', back_populates='post', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        db.Index('idx_user_scheduled_time', 'user_id', 'scheduled_time'),
        db.Index('idx_status_scheduled_time', 'status', 'scheduled_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'caption': self.caption,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
