from app.extensions import db
from datetime import datetime, timezone
import bcrypt


# Association table — many-to-many between users and roles
user_roles = db.Table(
    'user_roles',
    db.Column('user_id',     db.Integer, db.ForeignKey('users.id',  ondelete='CASCADE'), primary_key=True),
    db.Column('role_id',     db.Integer, db.ForeignKey('roles.id',  ondelete='CASCADE'), primary_key=True),
    db.Column('assigned_at', db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    papers = db.relationship('Paper', backref='author', lazy=True)
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        lazy='subquery',
        backref=db.backref('users', lazy=True),
    )

    # ── Password helpers ───────────────────────────────────────────

    def set_password(self, password):
        """Hash and store password — plain text is never saved."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Verify a plain-text password against the stored hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # ── RBAC helpers ───────────────────────────────────────────────

    def has_role(self, role_name: str) -> bool:
        """Return True if the user has been assigned the named role."""
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """Return True if any of the user's roles grants this permission."""
        return any(
            p.name == permission_name
            for r in self.roles
            for p in r.permissions
        )

    def get_all_permissions(self) -> set:
        """Return the full set of permission names across all assigned roles."""
        return {p.name for r in self.roles for p in r.permissions}

    # ── Serialisation ──────────────────────────────────────────────

    def to_dict(self):
        """Safe representation — password_hash is never exposed."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'roles': [r.name for r in self.roles],
            'permissions': sorted(self.get_all_permissions()),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<User {self.username}>'
