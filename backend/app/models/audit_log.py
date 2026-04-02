from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id            = db.Column(db.Integer, primary_key=True)
    timestamp     = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    user_id       = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    action        = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50),  nullable=True)
    resource_id   = db.Column(db.Integer,     nullable=True)
    details       = db.Column(db.JSON,        nullable=True)
    ip_address    = db.Column(db.String(45),  nullable=True)
    status        = db.Column(db.String(20),  nullable=False, default='success')

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id':            self.id,
            'timestamp':     self.timestamp.isoformat(),
            'user_id':       self.user_id,
            'action':        self.action,
            'resource_type': self.resource_type,
            'resource_id':   self.resource_id,
            'details':       self.details,
            'ip_address':    self.ip_address,
            'status':        self.status,
        }
