from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime
from ..utils.encryption import encrypt_token, decrypt_token, mask_token


class UserPlatform(db.Model):
    __tablename__ = 'user_platforms'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('users.id')), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('social_platforms.id')), nullable=False)
    platform_user_id = db.Column(db.String(255))
    _access_token = db.Column('access_token', db.Text)
    _refresh_token = db.Column('refresh_token', db.Text)
    token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='user_platforms')
    platform = db.relationship('SocialPlatform', back_populates='user_platforms')
    
    # Encrypted token properties
    @property
    def access_token(self):
        """Get decrypted access token."""
        return decrypt_token(self._access_token)
    
    @access_token.setter
    def access_token(self, value):
        """Set encrypted access token."""
        self._access_token = encrypt_token(value)
    
    @property
    def refresh_token(self):
        """Get decrypted refresh token."""
        return decrypt_token(self._refresh_token)
    
    @refresh_token.setter
    def refresh_token(self, value):
        """Set encrypted refresh token."""
        self._refresh_token = encrypt_token(value)

    # Schema and Indexes
    schema_args = {'schema': SCHEMA} if environment == "production" else {}
    __table_args__ = (
        db.Index('idx_user_platform_unique', 'user_id', 'platform_id', 'platform_user_id', unique=True),
        db.Index('idx_user_platform', 'user_id', 'platform_id'),
        db.Index('idx_token_expiry', 'token_expiry'),
        schema_args,  # dict must be the last element
    )

    def to_dict(self, include_tokens=False):
        """
        Convert to dictionary representation.
        
        Args:
            include_tokens (bool): Whether to include actual tokens (for internal use only)
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'platform_id': self.platform_id,
            'platform_user_id': self.platform_user_id,
            'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_tokens:
            # Only include actual tokens for internal API use
            data['access_token'] = self.access_token
            data['refresh_token'] = self.refresh_token
        else:
            # Include masked tokens for external API responses
            data['access_token'] = mask_token(self.access_token) if self.access_token else None
            data['refresh_token'] = mask_token(self.refresh_token) if self.refresh_token else None
        
        return data
