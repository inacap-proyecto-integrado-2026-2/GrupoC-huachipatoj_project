from django.utils import timezone
from .models import Justificativo, Prestamo, Autorizacion


def sidebar_counts(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}
    return {
        'nav_pending_docs': Justificativo.objects.filter(estado='pendiente').count(),
        'nav_pending_auth': Autorizacion.objects.filter(estado='pendiente').count(),
        'nav_active_loans': Prestamo.objects.filter(devuelto__isnull=True).count(),
        'nav_today': timezone.localdate(),
    }
