from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime


class SocialPlatform(db.Model):
    __tablename__ = 'social_platforms'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_base_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_platforms = db.relationship('UserPlatform', back_populates='platform', cascade='all, delete-orphan')
    post_platforms = db.relationship('PostPlatform', back_populates='platform', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'api_base_url': self.api_base_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
