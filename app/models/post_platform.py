from .db import db, environment, SCHEMA, add_prefix_for_prod
import uuid
from datetime import datetime


class PostPlatform(db.Model):
    __tablename__ = 'post_platforms'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('posts.id')), nullable=False)
    platform_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('social_platforms.id')), nullable=False)
    platform_caption = db.Column(db.Text)
    media_urls = db.Column(db.JSON)  # [{url, type, alt, poster}]
    platform_post_id = db.Column(db.String(255))  # returned id from the platform
    status = db.Column(db.String(50), nullable=False)  # pending|queued|publishing|published|failed|skipped
    published_at = db.Column(db.DateTime)

    # Relationships
    post = db.relationship('Post', back_populates='post_platforms')
    platform = db.relationship('SocialPlatform', back_populates='post_platforms')

    # Indexes
    __table_args__ = (
        db.Index('idx_post_platform_unique', 'post_id', 'platform_id', unique=True),
        db.Index('idx_status', 'status'),
        db.Index('idx_platform_post_id', 'platform_post_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'platform_id': self.platform_id,
            'platform_caption': self.platform_caption,
            'media_urls': self.media_urls,
            'platform_post_id': self.platform_post_id,
            'status': self.status,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
