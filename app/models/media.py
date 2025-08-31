from .db import db, environment, SCHEMA, add_prefix_for_prod
import uuid
from datetime import datetime


class Media(db.Model):
    __tablename__ = 'media'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)  # image|video|gif|audio|document
    url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='media')
    post_media = db.relationship('PostMedia', back_populates='media', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        db.Index('idx_user_created_at', 'user_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'media_type': self.media_type,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
