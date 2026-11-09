from django.utils import timezone
from .models import Justificativo, Prestamo, Autorizacion
from .roles import get_user_role, can_manage_sensitive, is_club_admin


def sidebar_counts(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}
    sensitive = can_manage_sensitive(user)
    return {
        'nav_pending_docs': Justificativo.objects.filter(estado='pendiente').count() if sensitive else 0,
        'nav_pending_auth': Autorizacion.objects.filter(estado='pendiente').count() if sensitive else 0,
        'nav_active_loans': Prestamo.objects.filter(devuelto__isnull=True).count(),
        'nav_today': timezone.localdate(),
        'nav_user_role': get_user_role(user),
        'nav_can_sensitive': sensitive,
        'nav_is_admin': is_club_admin(user),
    }
