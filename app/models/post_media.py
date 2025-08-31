from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime


class PostMedia(db.Model):
    __tablename__ = 'post_media'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    post_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('posts.id')), primary_key=True)
    media_id = db.Column(db.String(36), db.ForeignKey(add_prefix_for_prod('media.id')), primary_key=True)
    sort_order = db.Column(db.Integer)  # optional ordering for composer/publisher
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    post = db.relationship('Post', back_populates='post_media')
    media = db.relationship('Media', back_populates='post_media')

    # Indexes
    __table_args__ = (
        db.Index('idx_post_sort_order', 'post_id', 'sort_order'),
        db.Index('idx_media_id', 'media_id'),
    )

    def to_dict(self):
        return {
            'post_id': self.post_id,
            'media_id': self.media_id,
            'sort_order': self.sort_order,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }
