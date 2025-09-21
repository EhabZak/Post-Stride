from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime


class PostPlatform(db.Model):
    __tablename__ = 'post_platforms'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('posts.id')), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('social_platforms.id')), nullable=False)
    platform_caption = db.Column(db.Text)
    media_urls = db.Column(db.JSON)  # [{url, type, alt, poster}]
    platform_post_id = db.Column(db.String(255))  # returned id from the platform
    status = db.Column(db.String(50), nullable=False)  # pending|queued|publishing|published|failed|skipped
    published_at = db.Column(db.DateTime)

    # Relationships
    post = db.relationship('Post', back_populates='post_platforms')
    platform = db.relationship('SocialPlatform', back_populates='post_platforms')

    # Schema and Indexes
    schema_args = {'schema': SCHEMA} if environment == "production" else {}
    __table_args__ = (
        db.Index('idx_post_platform_unique', 'post_id', 'platform_id', unique=True),
        db.Index('idx_status', 'status'),
        db.Index('idx_platform_post_id', 'platform_post_id'),
        schema_args,  # dict must be the last element
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
