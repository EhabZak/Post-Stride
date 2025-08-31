from .db import db, environment, SCHEMA, add_prefix_for_prod
import uuid
from datetime import datetime


class UserPlatform(db.Model):
    __tablename__ = 'user_platforms'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    platform_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('social_platforms.id')), nullable=False)
    platform_user_id = db.Column(db.String(255))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='user_platforms')
    platform = db.relationship('SocialPlatform', back_populates='user_platforms')

    # Indexes
    __table_args__ = (
        db.Index('idx_user_platform_unique', 'user_id', 'platform_id', 'platform_user_id', unique=True),
        db.Index('idx_user_platform', 'user_id', 'platform_id'),
        db.Index('idx_token_expiry', 'token_expiry'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'platform_id': self.platform_id,
            'platform_user_id': self.platform_user_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
