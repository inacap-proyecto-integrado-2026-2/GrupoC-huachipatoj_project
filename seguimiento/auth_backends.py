from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from .forms import validar_y_formatear_rut

User = get_user_model()


class RutAuthenticationBackend(ModelBackend):
    """Permite que deportistas e apoderados inicien sesión escribiendo el RUT con o sin puntos ni guión."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            rut_formateado = validar_y_formatear_rut(username)
        except ValidationError:
            return None
        if rut_formateado == username:
            return None
        try:
            user = User.objects.get(username=rut_formateado)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
