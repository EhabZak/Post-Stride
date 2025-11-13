from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime


class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)  # image|video|gif|audio|document
    url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='media')
    post_media = db.relationship('PostMedia', back_populates='media', cascade='all, delete-orphan')

    # Schema and Indexes
    schema_args = {'schema': SCHEMA} if environment == "production" else {}
    __table_args__ = (
        db.Index('idx_user_created_at', 'user_id', 'created_at'),
        schema_args,  # dict must be the last element
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'media_type': self.media_type,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
