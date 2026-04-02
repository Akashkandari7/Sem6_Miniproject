from app import create_app
from app.extensions import db
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

def update_db():
    app = create_app()
    with app.app_context():
        # 1. Define all permissions
        _PERMISSIONS = [
            ('questions.create',      'questions', 'create',       'Add questions to the bank'),
            ('questions.read',        'questions', 'read',         'View questions'),
            ('questions.update',      'questions', 'update',       'Edit existing questions'),
            ('questions.delete',      'questions', 'delete',       'Remove questions from the bank'),
            ('questions.generate_ai', 'questions', 'generate_ai',  'Generate questions via AI'),
            ('papers.create',         'papers',    'create',       'Generate exam papers'),
            ('papers.read',           'papers',    'read',         'View exam papers'),
            ('papers.update',         'papers',    'update',       'Edit paper questions'),
            ('papers.delete',         'papers',    'delete',       'Delete exam papers'),
            ('papers.download_pdf',   'papers',    'download_pdf', 'Download paper as PDF'),
            ('subjects.create',       'subjects',  'create',       'Create subjects'),
            ('subjects.read',         'subjects',  'read',         'View subjects'),
            ('subjects.update',       'subjects',  'update',       'Edit subjects'),
            ('subjects.delete',       'subjects',  'delete',       'Delete subjects'),
            ('users.read_self',       'users',     'read_self',    'View own profile'),
            ('users.list',            'users',     'list',         'List all users'),
            ('users.create',          'users',     'create',       'Create user accounts'),
            ('users.update',          'users',     'update',       'Edit user accounts'),
            ('users.delete',          'users',     'delete',       'Delete user accounts'),
            ('users.assign_subjects', 'users',     'assign_subjects', 'Assign subjects to teachers'),
        ]

        perm_map = {}
        for name, resource, action, desc in _PERMISSIONS:
            p = Permission.query.filter_by(name=name).first()
            if not p:
                p = Permission(name=name, resource=resource, action=action, description=desc)
                db.session.add(p)
                print(f"Added permission: {name}")
            else:
                p.description = desc # sync description
            perm_map[name] = p

        db.session.flush()

        # 2. Define Roles
        def _get_perms(*names):
            return [perm_map[n] for n in names]

        # Admin
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Full access to all resources')
            db.session.add(admin_role)
        admin_role.permissions = list(perm_map.values())

        # Teacher
        teacher_role = Role.query.filter_by(name='teacher').first()
        if not teacher_role:
            teacher_role = Role(name='teacher', description='Manage questions, papers, and view subjects')
            db.session.add(teacher_role)
        teacher_role.permissions = _get_perms(
            'questions.create', 'questions.read', 'questions.update',
            'questions.delete', 'questions.generate_ai',
            'papers.create', 'papers.read', 'papers.update',
            'papers.delete', 'papers.download_pdf',
            'subjects.read',
            'users.read_self',
        )

        db.session.commit()
        print("RBAC data updated successfully.")

        # 3. Fix the admin user (admin@test.com based on browser subagent attempt)
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                db.session.commit()
                print(f"Assigned admin role to {admin_user.username}")

if __name__ == "__main__":
    update_db()
