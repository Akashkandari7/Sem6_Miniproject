from app.extensions import db


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    # Canonical dot-separated name used in code: e.g. 'questions.create'
    name = db.Column(db.String(64), unique=True, nullable=False)
    resource = db.Column(db.String(32), nullable=False)  # 'questions', 'papers', ...
    action = db.Column(db.String(32), nullable=False)    # 'create', 'read', ...
    description = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'resource': self.resource,
            'action': self.action,
            'description': self.description,
        }

    def __repr__(self):
        return f'<Permission {self.name}>'
