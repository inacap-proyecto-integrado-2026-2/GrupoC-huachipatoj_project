from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

ROL_ADMIN = 'Administrador'
ROL_ENTRENADOR = 'Entrenador'
ROL_ASISTENTE = 'Asistente'

STAFF_ROLES = [
    (ROL_ENTRENADOR, 'Entrenador Titular'),
    (ROL_ASISTENTE, 'Profesor Asistente'),
    (ROL_ADMIN, 'Administrador del Club'),
]
VALID_STAFF_ROLE_CODES = {code for code, _ in STAFF_ROLES}


def get_user_role(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return 'Anónimo'
    if not user.is_staff:
        return 'Alumno'
    if user.is_superuser:
        return ROL_ADMIN
    group_names = set(user.groups.values_list('name', flat=True))
    if ROL_ADMIN in group_names:
        return ROL_ADMIN
    if ROL_ENTRENADOR in group_names:
        return ROL_ENTRENADOR
    if ROL_ASISTENTE in group_names:
        return ROL_ASISTENTE
    # Cuentas is_staff heredadas sin grupo asignado operan como Entrenador Titular.
    return ROL_ENTRENADOR


def can_manage_sensitive(user):
    return bool(user and user.is_authenticated and user.is_staff and get_user_role(user) in (ROL_ADMIN, ROL_ENTRENADOR))


def is_club_admin(user):
    return bool(user and user.is_authenticated and user.is_staff and get_user_role(user) == ROL_ADMIN)


def assign_staff_role(user, role_code):
    if role_code not in VALID_STAFF_ROLE_CODES:
        raise ValueError(f'Rol inválido: {role_code}')
    old_groups = list(Group.objects.filter(name__in=VALID_STAFF_ROLE_CODES))
    if old_groups:
        user.groups.remove(*old_groups)
    target_group, _ = Group.objects.get_or_create(name=role_code)
    user.groups.add(target_group)


def role_required(*allowed_roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_staff or get_user_role(request.user) not in allowed_roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
