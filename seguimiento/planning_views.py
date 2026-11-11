from .filters import apply_filters
import calendar
import csv
from datetime import date, timedelta
from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .models import ClaseEntrenamiento, Evaluacion, Jugador, Autorizacion
from .pilot_views import coach, coach_titular, log, DocumentForm, _csv_safe, _sha256_file, _client_ip


class SessionForm(forms.ModelForm):
    semanas = forms.IntegerField(
        min_value=1,
        max_value=12,
        initial=1,
        required=False,
        label='Repetir semanalmente (cantidad de clases)',
        help_text='Deja en 1 para crear solo esta fecha, o elige entre 2 y 12 semanas seguidas en el mismo horario.',
    )

    class Meta:
        model = ClaseEntrenamiento
        fields = ['fecha', 'hora', 'categoria', 'profesor', 'objetivo', 'estado']
        labels = {'profesor': 'Entrenador', 'categoria': 'Categoría'}
        widgets = {'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}), 'hora': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ['hora', 'categoria', 'objetivo']:
            self.fields[key].required = True
        self.original = ClaseEntrenamiento.objects.filter(pk=self.instance.pk).first() if self.instance.pk else None
        if self.original:
            self.fields.pop('semanas', None)

    def clean(self):
        data = super().clean()
        semanas = data.get('semanas') or 1
        if data.get('estado') == 'realizada' and data.get('fecha') and data['fecha'] > timezone.localdate():
            self.add_error('estado', 'Una clase futura no puede marcarse realizada.')
        if not self.original and semanas > 1 and data.get('estado') == 'realizada':
            self.add_error('semanas', 'Para programar múltiples semanas seguidas, deja el estado en Programada.')
        if self.original and self.original.evaluacion_set.exists():
            if data.get('fecha') != self.original.fecha or data.get('categoria') != self.original.categoria:
                raise forms.ValidationError('Esta clase ya tiene registros. Conserva su fecha y categoría para proteger el historial; puedes cancelarla.')
            if data.get('estado') == 'programada':
                self.add_error('estado', 'Una clase con registros no puede volver a programada.')
        return data


@coach
def session_edit(request, pk=None):
    instance = get_object_or_404(ClaseEntrenamiento, pk=pk) if pk else None
    form = SessionForm(
        request.POST if request.method == 'POST' else None,
        instance=instance,
        initial=({'fecha': timezone.localdate(), 'estado': 'programada', 'profesor': request.user.get_full_name() or request.user.username} if not instance else {}),
    )
    # Las clases históricas sin categoría pueden conservar ese dato desconocido.
    if instance and not instance.categoria:
        form.fields['categoria'].required = False
    if request.method == 'POST' and form.is_valid():
        semanas = (form.cleaned_data.get('semanas') or 1) if not instance else 1
        with transaction.atomic():
            obj = form.save()
            log(request, f'Guardó clase {obj.pk}: {obj.estado}')
            if not instance and semanas > 1:
                for step in range(1, semanas):
                    extra = ClaseEntrenamiento.objects.create(
                        fecha=obj.fecha + timedelta(days=7 * step),
                        hora=obj.hora,
                        categoria=obj.categoria,
                        profesor=obj.profesor,
                        objetivo=obj.objetivo,
                        estado=obj.estado,
                    )
                    log(request, f'Programó clase periódica {extra.pk}')
        if not instance and semanas > 1:
            messages.success(request, f'Se programaron {semanas} entrenamientos semanales a partir del {obj.fecha}.')
        else:
            messages.success(request, 'Clase guardada. Las cancelaciones conservan su historial.')
        return redirect('/calendario/?fecha=' + obj.fecha.isoformat())
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Editar clase' if pk else 'Programar clase',
            'ayuda': 'Programa una clase individual o repítela semanalmente hasta 12 fechas. Marca Realizada al impartirla; Cancelada conserva los registros y los excluye de promedios.',
            'cancel_url': reverse('calendario'),
        },
    )


@coach
def schedule(request):
    try:
        anchor = date.fromisoformat(request.GET.get('fecha', timezone.localdate().isoformat()))
    except ValueError:
        anchor = timezone.localdate()
    mode = request.GET.get('vista', 'mes')
    mode = mode if mode in ('mes', 'semana', 'lista') else 'mes'
    month_start = anchor.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    if mode == 'semana':
        start = anchor - timedelta(days=anchor.weekday())
        end = start + timedelta(days=7)
        prev = start - timedelta(days=7)
        nxt = end
        weeks = [[start + timedelta(days=i) for i in range(7)]]
    else:
        start = month_start
        end = next_month
        prev = month_start - timedelta(days=1)
        nxt = next_month
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(anchor.year, anchor.month)
    rows = ClaseEntrenamiento.objects.filter(fecha__gte=start, fecha__lt=end).order_by('fecha', 'hora', 'id')
    category = request.GET.get('categoria', '')
    if category:
        rows = rows.filter(categoria=category)
    rows, filters = apply_filters(request, rows, 'calendar')
    by_day = {}
    for s in rows:
        by_day.setdefault(s.fecha, []).append(s)
    grid = [[(d, by_day.get(d, []), d.month == anchor.month) for d in week] for week in weeks]
    return render(
        request,
        'seguimiento/calendar.html',
        {
            'filters': filters, 'result_count': rows.count(),
            'clases': rows,
            'grid': grid,
            'vista': mode,
            'anchor': anchor,
            'prev': prev,
            'next': nxt,
            'categoria': category,
            'categorias': Jugador.CATEGORIAS,
            'start': start,
            'end': end - timedelta(days=1),
        },
    )


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ['observacion_privada']
        labels = {'observacion_privada': 'Observación privada del entrenamiento'}
        widgets = {'observacion_privada': forms.Textarea(attrs={'rows': 5, 'maxlength': 3000})}

    def clean_observacion_privada(self):
        text = self.cleaned_data['observacion_privada']
        if len(text) > 3000:
            raise forms.ValidationError('Máximo 3000 caracteres.')
        return text


@coach
def observation(request, pk):
    e = get_object_or_404(Evaluacion.objects.select_related('jugador', 'clase'), pk=pk)
    form = ObservationForm(request.POST if request.method == 'POST' else None, instance=e)
    pista_url = f"{reverse('pista')}?sesion={e.clase_id}"
    if request.method == 'POST' and form.is_valid():
        form.save()
        log(request, f'Editó observación privada de evaluación {pk}')
        messages.success(request, f'Observación privada guardada para {e.jugador.nombre_completo}.')
        return redirect(pista_url)
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Observación de ' + e.jugador.nombre_completo,
            'ayuda': f'Clase del {e.clase.fecha}. Solo visible para el cuerpo técnico; no se incluye en reportes PDF ni en la vista del alumno.',
            'cancel_url': pista_url,
        },
    )


class AuthorizationForm(forms.ModelForm):
    class Meta:
        model = Autorizacion
        fields = ['jugador', 'apoderado', 'fecha', 'responsable', 'estado', 'archivo']
        labels = {'fecha': 'Fecha de autorización', 'responsable': 'Responsable del registro', 'archivo': 'Documento firmado PDF o JPG (máx. 4 MB)'}
        widgets = {'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def clean_archivo(self):
        f = self.cleaned_data['archivo']
        if not hasattr(f, 'content_type'):
            return f
        return DocumentForm.clean_archivo(self)

    def clean_fecha(self):
        day = self.cleaned_data['fecha']
        if day > timezone.localdate():
            raise forms.ValidationError('La autorización no puede tener fecha futura.')
        return day


@coach_titular
def authorizations(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    rows = Autorizacion.objects.select_related('jugador').order_by('-fecha', '-id')
    if q:
        rows = rows.filter(
            Q(jugador__nombre_completo__icontains=q)
            | Q(jugador__rut__icontains=q)
            | Q(apoderado__icontains=q)
        )
    if estado in ('pendiente', 'vigente', 'revocada'):
        rows = rows.filter(estado=estado)
    rows, filters = apply_filters(request, rows, 'authorizations')
    return render(
        request,
        'seguimiento/authorizations.html',
        {
            'filters': filters, 'result_count': rows.count(),
            'autorizaciones': rows,
            'q': q,
            'estado': estado,
            'estados': Autorizacion._meta.get_field('estado').choices,
        },
    )


@coach_titular
def authorization_edit(request, pk=None):
    instance = get_object_or_404(Autorizacion, pk=pk) if pk else None
    old_file_name = instance.archivo.name if instance and instance.archivo else None
    form = AuthorizationForm(
        request.POST if request.method == 'POST' else None,
        request.FILES or None,
        instance=instance,
        initial=({'fecha': timezone.localdate(), 'responsable': request.user.get_full_name() or request.user.username} if not instance else {}),
    )
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if 'archivo' in form.changed_data:
            obj.hash_documento = _sha256_file(form.cleaned_data['archivo'])
        if not instance or 'archivo' in form.changed_data:
            obj.ip_registro = _client_ip(request)
        obj.save()
        if 'archivo' in form.changed_data and old_file_name and old_file_name != obj.archivo.name:
            try:
                obj.archivo.storage.delete(old_file_name)
            except Exception:
                pass
        log(request, f'Guardó autorización {obj.pk}: {obj.estado}')
        messages.success(request, f'Autorización de {obj.jugador.nombre_completo} guardada ({obj.get_estado_display()}).')
        return redirect('autorizaciones')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Autorización de apoderado',
            'ayuda': 'Registro documental restringido al cuerpo técnico titular. Adjunta PDF o JPG de hasta 4 MB. Al subir el archivo se calcula su huella SHA-256 de integridad.',
            'cancel_url': reverse('autorizaciones'),
        },
    )


@coach_titular
def authorization_file(request, pk):
    obj = get_object_or_404(Autorizacion, pk=pk)
    log(request, f'Descargó autorización {pk}')
    return FileResponse(obj.archivo.open('rb'), as_attachment=True, filename=f'autorizacion-{pk}.{obj.archivo.name.rsplit(".", 1)[-1]}')


class ReportForm(forms.Form):
    mes = forms.DateField(label='Mes del informe', input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month'}))
    jugador = forms.ModelChoiceField(queryset=Jugador.objects.order_by('nombre_completo'), required=False)
    categoria = forms.ChoiceField(choices=[('', 'Selecciona categoría')] + Jugador.CATEGORIAS, required=False)

    def clean(self):
        data = super().clean()
        if bool(data.get('jugador')) == bool(data.get('categoria')):
            raise forms.ValidationError('Selecciona un jugador o una categoría, solo una opción.')
        return data


@coach
def reports(request):
    form = ReportForm(request.GET if request.GET else None, initial={'mes': timezone.localdate().replace(day=1)})
    if request.GET and form.is_valid():
        data = form.cleaned_data
        fmt = request.GET.get('formato', 'pdf').lower()
        if fmt == 'csv':
            from .report_pdf import report_data
            rows, _, _ = report_data(data['mes'], data.get('jugador'), data.get('categoria'))
            log(request, 'Exportó reporte mensual CSV ' + data['mes'].strftime('%Y-%m'))
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="Huachipato-' + data['mes'].strftime('%Y-%m') + '.csv"'
            response['Cache-Control'] = 'private, no-store'
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow(['Fecha', 'Clase ID', 'Estado clase', 'Categoría', 'Jugador', 'Asistencia', 'Frenado', 'Pase', 'Tiro'])
            for e in rows:
                scored = e.clase.estado == 'realizada' and e.asistencia in ('P', 'T')
                writer.writerow([
                    e.clase.fecha.isoformat(),
                    e.clase_id,
                    _csv_safe(e.clase.get_estado_display()),
                    _csv_safe(e.get_categoria_registrada_display() or e.jugador.get_categoria_display()),
                    _csv_safe(e.jugador.nombre_completo),
                    _csv_safe(e.get_asistencia_display()),
                    e.nota_frenado if scored and e.nota_frenado > 0 else '',
                    e.nota_pase if scored and e.nota_pase > 0 else '',
                    e.nota_tiro if scored and e.nota_tiro > 0 else '',
                ])
            return response

        from .report_pdf import build_report
        content = build_report(data['mes'], data.get('jugador'), data.get('categoria'))
        log(request, 'Exportó reporte mensual ' + data['mes'].strftime('%Y-%m'))
        response = HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Huachipato-' + data['mes'].strftime('%Y-%m') + '.pdf"'
        response['Cache-Control'] = 'private, no-store'
        return response
    return render(request, 'seguimiento/reports.html', {'form': form})
