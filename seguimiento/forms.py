import re
from django import forms
from .models import Jugador


def limpiar_rut(rut: str) -> str:
    """Elimina espacios, puntos y guiones, dejando dígitos y DV en mayúscula."""
    return re.sub(r'[\s.\-]', '', (rut or '').strip()).upper()


def calcular_dv(cuerpo: str) -> str:
    """Calcula el dígito verificador chileno mediante algoritmo Módulo 11."""
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def validar_y_formatear_rut(valor: str) -> str:
    """Valida un RUT chileno con Módulo 11 y lo normaliza a formato XX.XXX.XXX-Y."""
    limpio = limpiar_rut(valor)
    if not re.fullmatch(r'\d{6,8}[0-9K]', limpio):
        raise forms.ValidationError(
            'Formato de RUT inválido. Ingresa 6 a 8 dígitos y su dígito verificador (ej: 12.345.678-5).'
        )

    cuerpo, dv = limpio[:-1], limpio[-1]
    if int(cuerpo) == 0:
        raise forms.ValidationError('El RUT ingresado no puede ser cero.')

    dv_esperado = calcular_dv(cuerpo)
    if dv != dv_esperado:
        raise forms.ValidationError(
            'RUT inválido. El dígito verificador no coincide según el algoritmo Módulo 11.'
        )

    cuerpo_formateado = f'{int(cuerpo):,}'.replace(',', '.')
    return f'{cuerpo_formateado}-{dv}'


class JugadorForm(forms.ModelForm):
    rut = forms.CharField(
        max_length=20,
        label='RUT del deportista',
        help_text='Formato chileno validado con Módulo 11 (ej: 12.345.678-5).',
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-5',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = Jugador
        fields = [
            'rut',
            'nombre_completo',
            'categoria',
            'fecha_nacimiento',
            'contacto_emergencia',
            'observaciones',
        ]
        labels = {
            'nombre_completo': 'Nombre completo',
            'categoria': 'Categoría',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'contacto_emergencia': 'Teléfono de emergencia',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe una observación inicial para el deportista...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['rut'].widget.attrs['readonly'] = True
            self.fields['rut'].help_text = 'El RUT vincula la cuenta del jugador. No se puede cambiar en esta versión.'

    def clean_rut(self):
        raw_rut = (self.cleaned_data.get('rut') or '').strip()

        if self.instance and self.instance.pk:
            old_rut = self.instance.rut
            if old_rut.startswith('DEMO-'):
                if raw_rut == old_rut:
                    return old_rut
                raise forms.ValidationError(
                    'El RUT vincula la cuenta del jugador. No se puede cambiar en esta versión.'
                )
            rut_formateado = validar_y_formatear_rut(raw_rut)
            if rut_formateado != old_rut:
                raise forms.ValidationError(
                    'El RUT vincula la cuenta del jugador. No se puede cambiar en esta versión.'
                )
            return rut_formateado

        rut_formateado = validar_y_formatear_rut(raw_rut)
        if Jugador.objects.filter(rut=rut_formateado).exists():
            raise forms.ValidationError('Ya existe un deportista registrado con este RUT.')
        return rut_formateado
