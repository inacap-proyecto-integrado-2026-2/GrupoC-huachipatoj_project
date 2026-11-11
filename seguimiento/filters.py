from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Jugador

class SearchFilters(forms.Form):
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        data = super().clean()
        if data.get('desde') and data.get('hasta') and data['desde'] > data['hasta']:
            raise forms.ValidationError('Desde no puede ser posterior a Hasta.')
        return data

def apply_filters(request, qs, kind):
    form = SearchFilters(request.GET)
    def choice(name, label, options):
        form.fields[name] = forms.ChoiceField(label=label, required=False, choices=[('', 'Todos')] + options)
    if kind in ('documents', 'authorizations'):
        choice('categoria', 'Categoría', Jugador.CATEGORIAS)
    if kind == 'documents':
        choice('fecha_tipo', 'Fecha a consultar', [('carga', 'Fecha de carga'), ('clase', 'Fecha de clase')])
    if kind == 'routines':
        form.fields['vencidas'] = forms.BooleanField(label='Solo pendientes vencidas', required=False)
    if kind in ('players', 'inventory', 'calendar'):
        form.fields.pop('desde'); form.fields.pop('hasta')
    if kind == 'players':
        choice('cuenta', 'Cuenta de acceso', [('activa', 'Activa'), ('desactivada', 'Desactivada'), ('sin', 'Sin cuenta')])
    if kind == 'inventory':
        choice('condicion', 'Estado del equipo', [('bueno', 'Bueno'), ('desgastado', 'Desgastado'), ('reparacion', 'En reparación')])
        choice('disponibilidad', 'Disponibilidad', [('libre', 'Libre'), ('prestado', 'Prestado')])
    if kind == 'calendar':
        choice('estado', 'Estado', [('programada', 'Programada'), ('realizada', 'Realizada'), ('cancelada', 'Cancelada')])
    if not form.is_valid():
        return qs.none(), form
    d = form.cleaned_data
    field = {'documents': 'evaluacion__clase__fecha' if d.get('fecha_tipo') == 'clase' else 'creado__date', 'authorizations': 'fecha', 'routines': 'fecha', 'audit': 'fecha__date'}.get(kind)
    for key, lookup in [('desde', 'gte'), ('hasta', 'lte')]:
        if field and d.get(key): qs = qs.filter(**{field + '__' + lookup: d[key]})
    if d.get('categoria'):
        prefix = 'evaluacion__jugador__categoria' if kind == 'documents' else 'jugador__categoria'
        qs = qs.filter(**{prefix: d['categoria']})
    if d.get('vencidas'): qs = qs.filter(completada=False, fecha__lt=timezone.localdate())
    if d.get('cuenta'):
        accounts = User.objects.all()
        if d['cuenta'] != 'sin': accounts = accounts.filter(is_active=d['cuenta'] == 'activa')
        lookup = {'rut__in': accounts.values('username')}
        qs = qs.exclude(**lookup) if d['cuenta'] == 'sin' else qs.filter(**lookup)
    if d.get('condicion'): qs = qs.filter(estado=d['condicion'])
    if d.get('disponibilidad'):
        from .models import Prestamo
        lookup = {'pk__in': Prestamo.objects.filter(devuelto__isnull=True).values('equipo_id')}
        qs = qs.filter(**lookup) if d['disponibilidad'] == 'prestado' else qs.exclude(**lookup)
    if kind == 'calendar' and d.get('estado'): qs = qs.filter(estado=d['estado'])
    return qs, form
