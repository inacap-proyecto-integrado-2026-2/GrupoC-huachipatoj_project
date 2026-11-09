import csv
import json
import secrets
from datetime import timedelta
from functools import wraps
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from django.http import JsonResponse, FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Justificativo, Equipo, Prestamo, Rutina, Auditoria, Autorizacion
from .forms import JugadorForm


def coach(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def log(request, text):
    Auditoria.objects.create(usuario=request.user, accion=text)


def _csv_safe(value):
    text = '' if value is None else str(value)
    if text and text[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + text
    return text


def _skill_mean(rows, field):
    values = [
        getattr(e, field)
        for e in rows
        if e.clase.estado == 'realizada' and e.asistencia in ('P', 'T') and getattr(e, field) > 0
    ]
    return round(sum(values) / len(values), 1) if values else None


def _create_or_reset_player_account(player, *, reset=False):
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    raw_password = 'Cdh#' + ''.join(secrets.choice(alphabet) for _ in range(6))
    existing = User.objects.filter(username=player.rut).first()
    if existing:
        if existing.is_staff or existing.is_superuser or not reset:
            return existing, None, False
        existing.set_password(raw_password)
        if not existing.first_name and player.nombre_completo:
            existing.first_name = player.nombre_completo[:150]
        existing.save()
        return existing, raw_password, False
    user = User.objects.create_user(
        username=player.rut,
        password=raw_password,
        first_name=player.nombre_completo[:150],
        is_staff=False,
    )
    return user, raw_password, True


def _student_justificable_evaluaciones(player):
    if not player:
        return Evaluacion.objects.none()
    return (
        Evaluacion.objects.filter(jugador=player, asistencia__in=['A', 'T'])
        .exclude(justificativo__estado__in=['pendiente', 'aprobado'])
        .select_related('clase')
        .order_by('-clase__fecha', '-id')
    )


def _filtered_players(q, categoria):
    qs = Jugador.objects.order_by('nombre_completo')
    if q:
        qs = qs.filter(Q(nombre_completo__icontains=q) | Q(rut__icontains=q))
    if categoria:
        qs = qs.filter(categoria=categoria)
    return qs


@coach
def pista(request):
    sessions = ClaseEntrenamiento.objects.exclude(estado='cancelada').order_by('-fecha', '-id')
    session = (
        get_object_or_404(ClaseEntrenamiento, pk=request.GET['sesion'])
        if request.GET.get('sesion')
        else (sessions.filter(fecha__lte=timezone.localdate()).first() or sessions.first())
    )
    players_qs = Jugador.objects.order_by('nombre_completo')
    if session and session.categoria:
        players_qs = players_qs.filter(Q(categoria=session.categoria) | Q(evaluacion__clase=session)).distinct()
    category = request.GET.get('categoria', '')
    if category:
        players_qs = players_qs.filter(categoria=category)
    scores = {e.jugador_id: e for e in Evaluacion.objects.filter(clase=session)}
    filas = [(p, scores.get(p.pk)) for p in players_qs]
    evaluadas = sum(1 for _, e in filas if e is not None)
    return render(
        request,
        'seguimiento/pista.html',
        {
            'sesiones': sessions,
            'sesion': session,
            'filas': filas,
            'evaluadas': evaluadas,
            'total_filas': len(filas),
            'categorias': Jugador.CATEGORIAS,
            'categoria': category,
            'bloqueada': bool(session and (session.estado != 'realizada' or session.fecha > timezone.localdate())),
        },
    )


@login_required
def home(request):
    if not request.user.is_staff:
        player = Jugador.objects.filter(rut=request.user.username).first()
        evals_asc = (
            list(Evaluacion.objects.filter(jugador=player).select_related('clase').order_by('clase__fecha', 'id'))
            if player
            else []
        )
        chart = [
            {
                'fecha': str(e.clase.fecha),
                'frenado': e.nota_frenado or None,
                'pase': e.nota_pase or None,
                'tiro': e.nota_tiro or None,
            }
            for e in evals_asc
            if e.asistencia in ('P', 'T') and e.clase.estado == 'realizada'
        ]
        valid_evals = [e for e in evals_asc if e.clase.estado == 'realizada']
        present_count = sum(1 for e in valid_evals if e.asistencia in ('P', 'T'))
        avg_skills = [v for v in (_skill_mean(valid_evals, 'nota_frenado'), _skill_mean(valid_evals, 'nota_pase'), _skill_mean(valid_evals, 'nota_tiro')) if v is not None]
        avg_general = round(sum(avg_skills) / len(avg_skills), 1) if avg_skills else None
        routines_list = list(Rutina.objects.filter(jugador=player).order_by('completada', '-fecha')) if player else []
        justificativos_list = (
            list(Justificativo.objects.filter(evaluacion__jugador=player).select_related('evaluacion__clase').order_by('-creado')[:10])
            if player
            else []
        )
        return render(
            request,
            'seguimiento/student.html',
            {
                'player': player,
                'evaluaciones': list(reversed(evals_asc)),
                'chart': chart,
                'rutinas': routines_list,
                'justificativos': justificativos_list,
                'stat_presentes': present_count,
                'stat_evaluaciones': len(evals_asc),
                'stat_promedio': avg_general,
                'stat_rutinas_pendientes': sum(1 for r in routines_list if not r.completada),
                'stat_rutinas_completadas': sum(1 for r in routines_list if r.completada),
                'has_pending_evals': _student_justificable_evaluaciones(player).exists() if player else False,
            },
        )
    if 'sesion' in request.GET:
        return pista(request)

    today = timezone.localdate()
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)

    total_jugadores = Jugador.objects.count()
    raw_cats = dict(Jugador.objects.values_list('categoria').annotate(total=Count('id')))
    cat_breakdown = []
    for code, label in Jugador.CATEGORIAS:
        count = raw_cats.get(code, 0)
        pct = round((count / total_jugadores) * 100) if total_jugadores else 0
        cat_breakdown.append({'code': code, 'label': label, 'count': count, 'pct': pct})

    month_sessions = ClaseEntrenamiento.objects.filter(fecha__gte=month_start, fecha__lt=next_month)
    clases_realizadas = month_sessions.filter(estado='realizada').count()
    clases_programadas = month_sessions.filter(estado='programada').count()
    clases_canceladas = month_sessions.filter(estado='cancelada').count()

    latest_session = (
        ClaseEntrenamiento.objects.exclude(estado='cancelada').filter(fecha__lte=today).order_by('-fecha', '-id').first()
        or ClaseEntrenamiento.objects.exclude(estado='cancelada').order_by('-fecha', '-id').first()
    )
    latest_eval_count = 0
    latest_target_count = 0
    latest_pct = 0
    if latest_session:
        latest_eval_count = Evaluacion.objects.filter(clase=latest_session).count()
        if latest_session.categoria:
            latest_target_count = Jugador.objects.filter(
                Q(categoria=latest_session.categoria) | Q(evaluacion__clase=latest_session)
            ).distinct().count()
        else:
            latest_target_count = total_jugadores
        if latest_target_count:
            latest_pct = min(100, round((latest_eval_count / latest_target_count) * 100))

    upcoming_sessions = list(
        ClaseEntrenamiento.objects.filter(estado='programada', fecha__gte=today).order_by('fecha', 'hora', 'id')[:5]
    )

    pending_docs_qs = Justificativo.objects.filter(estado='pendiente').select_related('evaluacion__jugador', 'evaluacion__clase').order_by('-creado')
    pending_docs_count = pending_docs_qs.count()
    pending_docs = list(pending_docs_qs[:5])

    pending_auth_qs = Autorizacion.objects.filter(estado='pendiente').select_related('jugador').order_by('-creado')
    pending_auth_count = pending_auth_qs.count()
    pending_auths = list(pending_auth_qs[:5])

    active_loans_qs = Prestamo.objects.filter(devuelto__isnull=True).select_related('equipo', 'jugador').order_by('-fecha')
    active_loans_count = active_loans_qs.count()
    active_loans = list(active_loans_qs[:5])

    total_equipos = Equipo.objects.count()
    equipos_reparacion = Equipo.objects.filter(estado='reparacion').count()
    pending_routines_count = Rutina.objects.filter(completada=False).count()

    recent_session_ids = list(
        ClaseEntrenamiento.objects.filter(estado='realizada').order_by('-fecha', '-id').values_list('id', flat=True)[:10]
    )
    att_raw = dict(
        Evaluacion.objects.filter(clase_id__in=recent_session_ids).values_list('asistencia').annotate(total=Count('id'))
    ) if recent_session_ids else {}
    att_total = sum(att_raw.values())
    attendance_stats = []
    for code, label, css_class in [
        ('P', 'Presente', 'success'),
        ('T', 'Atraso', 'warning'),
        ('A', 'Ausente', 'danger'),
        ('J', 'Justificado', 'info'),
    ]:
        val = att_raw.get(code, 0)
        pct = round((val / att_total) * 100) if att_total else 0
        attendance_stats.append({'code': code, 'label': label, 'count': val, 'pct': pct, 'style': css_class})

    recent_audit = list(Auditoria.objects.select_related('usuario').order_by('-fecha')[:6])

    return render(
        request,
        'seguimiento/dashboard.html',
        {
            'today': today,
            'total_jugadores': total_jugadores,
            'cat_breakdown': cat_breakdown,
            'clases_realizadas': clases_realizadas,
            'clases_programadas': clases_programadas,
            'clases_canceladas': clases_canceladas,
            'latest_session': latest_session,
            'latest_eval_count': latest_eval_count,
            'latest_target_count': latest_target_count,
            'latest_pct': latest_pct,
            'upcoming_sessions': upcoming_sessions,
            'pending_docs': pending_docs,
            'pending_docs_count': pending_docs_count,
            'pending_auths': pending_auths,
            'pending_auth_count': pending_auth_count,
            'pending_total': pending_docs_count + pending_auth_count,
            'active_loans': active_loans,
            'active_loans_count': active_loans_count,
            'total_equipos': total_equipos,
            'equipos_reparacion': equipos_reparacion,
            'pending_routines_count': pending_routines_count,
            'attendance_stats': attendance_stats,
            'att_total': att_total,
            'recent_audit': recent_audit,
        },
    )


@coach
@require_POST
def new_session(request):
    return redirect('programar_clase')


@coach
@require_POST
def save_score(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        attendance = data['asistencia']
        if attendance not in ('P', 'A', 'T'):
            raise ValueError
        notes = {k: data[k] for k in ('nota_frenado', 'nota_pase', 'nota_tiro')}
        if any(type(v) is not int or not 0 <= v <= 10 for v in notes.values()):
            raise ValueError
        if attendance == 'A':
            notes = dict.fromkeys(notes, 0)
        player = get_object_or_404(Jugador, pk=data['jugador'])
        session = get_object_or_404(ClaseEntrenamiento, pk=data['sesion'])
        if session.estado != 'realizada' or session.fecha > timezone.localdate():
            return JsonResponse({'error': 'Marca la clase como realizada antes de evaluar.'}, status=409)
        if session.categoria and player.categoria != session.categoria and not Evaluacion.objects.filter(jugador=player, clase=session).exists():
            return JsonResponse({'error': 'El jugador no pertenece a esta categoría.'}, status=400)
        with transaction.atomic():
            existing = Evaluacion.objects.filter(jugador=player, clase=session).first()
            if existing and existing.asistencia == 'J':
                return JsonResponse({'error': 'La ausencia ya está justificada.'}, status=409)
            e, _ = Evaluacion.objects.update_or_create(jugador=player, clase=session, defaults={'asistencia': attendance, **notes})
            if not e.categoria_registrada:
                e.categoria_registrada = session.categoria or player.categoria
                e.save(update_fields=['categoria_registrada'])
            log(request, f'Evaluó jugador {player.pk} en entrenamiento {session.pk}')
        return JsonResponse({'ok': True, 'evaluacion': e.pk})
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)


@coach
def players(request):
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    rows = list(_filtered_players(q, categoria))
    ruts = [p.rut for p in rows]
    account_ruts = set(User.objects.filter(username__in=ruts).values_list('username', flat=True)) if ruts else set()
    auth_by_player = {}
    if rows:
        for auth in Autorizacion.objects.filter(jugador__in=rows).order_by('-fecha', '-id'):
            if auth.jugador_id not in auth_by_player:
                auth_by_player[auth.jugador_id] = auth
    for p in rows:
        p.tiene_cuenta = p.rut in account_ruts
        p.ultima_autorizacion = auth_by_player.get(p.pk)
    return render(
        request,
        'seguimiento/players.html',
        {
            'jugadores': rows,
            'q': q,
            'categoria': categoria,
            'categorias': Jugador.CATEGORIAS,
        },
    )


@coach
def export_players_csv(request):
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    rows = list(_filtered_players(q, categoria))
    ruts = [p.rut for p in rows]
    account_ruts = set(User.objects.filter(username__in=ruts).values_list('username', flat=True)) if ruts else set()
    auth_by_player = {}
    if rows:
        for auth in Autorizacion.objects.filter(jugador__in=rows).order_by('-fecha', '-id'):
            if auth.jugador_id not in auth_by_player:
                auth_by_player[auth.jugador_id] = auth.get_estado_display()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Huachipato-jugadores.csv"'
    response['Cache-Control'] = 'private, no-store'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['RUT', 'Nombre completo', 'Categoría', 'Fecha nacimiento', 'Contacto emergencia', 'Acceso portal', 'Autorización'])
    for p in rows:
        writer.writerow([
            _csv_safe(p.rut),
            _csv_safe(p.nombre_completo),
            _csv_safe(p.get_categoria_display()),
            _csv_safe(p.fecha_nacimiento.isoformat()),
            _csv_safe(p.contacto_emergencia),
            'Activa' if p.rut in account_ruts else 'Sin cuenta',
            _csv_safe(auth_by_player.get(p.pk, 'Sin registro')),
        ])
    log(request, f'Exportó nómina de jugadores CSV ({len(rows)} registros)')
    return response


@coach
def player_edit(request, pk=None):
    instance = get_object_or_404(Jugador, pk=pk) if pk else None
    old_rut = instance.rut if instance else None
    form = JugadorForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        if old_rut and old_rut != form.cleaned_data['rut']:
            form.add_error('rut', 'El RUT vincula la cuenta del jugador. No se puede cambiar en esta versión.')
        else:
            with transaction.atomic():
                obj = form.save()
                log(request, f'Guardó jugador {obj.pk}')
                if not instance and form.cleaned_data.get('crear_cuenta'):
                    _, raw_password, _ = _create_or_reset_player_account(obj, reset=False)
                    if raw_password:
                        log(request, f'Creó acceso portal para jugador {obj.pk}')
                        messages.success(
                            request,
                            f'Jugador {obj.nombre_completo} guardado. Cuenta creada — Usuario: {obj.rut} · Contraseña temporal: {raw_password}',
                        )
                    else:
                        messages.success(request, f'Jugador {obj.nombre_completo} guardado correctamente.')
                else:
                    if instance:
                        User.objects.filter(username=obj.rut, is_staff=False).update(first_name=obj.nombre_completo[:150])
                    messages.success(request, f'Jugador {obj.nombre_completo} guardado correctamente.')
            return redirect('jugadores')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Editar jugador' if pk else 'Agregar jugador',
            'cancel_url': reverse('jugadores'),
        },
    )


@coach
@require_POST
def player_access(request, pk):
    player = get_object_or_404(Jugador, pk=pk)
    with transaction.atomic():
        _, raw_password, created = _create_or_reset_player_account(player, reset=True)
        if raw_password is None:
            messages.warning(request, 'No es posible restablecer la clave de una cuenta perteneciente al cuerpo técnico.')
        else:
            action_text = 'Creó acceso portal' if created else 'Restableció clave portal'
            log(request, f'{action_text} para jugador {player.pk}')
            label = 'Acceso creado' if created else 'Contraseña temporal restablecida'
            messages.success(
                request,
                f'{label} para {player.nombre_completo} — Usuario: {player.rut} · Contraseña temporal: {raw_password}',
            )
    if request.POST.get('next') == 'historial':
        return redirect('historial', pk=player.pk)
    return redirect('jugadores')


@coach
def history(request, pk):
    player = get_object_or_404(Jugador, pk=pk)
    evaluations = Evaluacion.objects.filter(jugador=player).select_related('clase').order_by('clase__fecha', 'id')
    chart = [
        {'fecha': str(e.clase.fecha), 'frenado': e.nota_frenado or None, 'pase': e.nota_pase or None, 'tiro': e.nota_tiro or None}
        for e in evaluations
        if e.asistencia in ('P', 'T') and e.clase.estado == 'realizada'
    ]
    return render(
        request,
        'seguimiento/history.html',
        {
            'player': player,
            'evaluaciones': evaluations,
            'chart': chart,
            'rutinas': Rutina.objects.filter(jugador=player).order_by('-fecha'),
            'tiene_cuenta': User.objects.filter(username=player.rut).exists(),
        },
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Justificativo
        fields = ['evaluacion', 'motivo', 'archivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['evaluacion'].queryset = Evaluacion.objects.filter(asistencia__in=['A', 'T']).select_related('jugador', 'clase')
        self.fields['evaluacion'].label_from_instance = lambda e: f'{e.jugador.nombre_completo} · {e.clase.fecha} · sesión {e.clase_id}'

    def clean_archivo(self):
        file = self.cleaned_data['archivo']
        head = file.read(8)
        file.seek(0)
        ext = file.name.lower().rsplit('.', 1)[-1]
        if file.size > 10 * 1024 * 1024 or not ((ext == 'pdf' and head.startswith(b'%PDF-')) or (ext in ('jpg', 'jpeg') and head.startswith(b'\xff\xd8\xff'))):
            raise forms.ValidationError('Adjunta un PDF o JPG válido de hasta 10 MB.')
        return file


class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = Justificativo
        fields = ['evaluacion', 'motivo', 'archivo']
        labels = {
            'evaluacion': 'Entrenamiento con ausencia o atraso',
            'motivo': 'Motivo',
            'archivo': 'Respaldo PDF o JPG (máx. 10 MB)',
        }

    def __init__(self, player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['evaluacion'].queryset = _student_justificable_evaluaciones(player)
        self.fields['evaluacion'].label_from_instance = (
            lambda e: f'{e.clase.fecha} · {e.get_asistencia_display()} · sesión #{e.clase_id}'
        )

    def clean_archivo(self):
        return DocumentForm.clean_archivo(self)


@coach
def documents(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    qs = Justificativo.objects.select_related('evaluacion__jugador', 'evaluacion__clase').order_by('-creado')
    if q:
        qs = qs.filter(
            Q(evaluacion__jugador__nombre_completo__icontains=q)
            | Q(evaluacion__jugador__rut__icontains=q)
            | Q(motivo__icontains=q)
        )
    if estado in ('pendiente', 'aprobado', 'rechazado'):
        qs = qs.filter(estado=estado)
    return render(
        request,
        'seguimiento/documents.html',
        {
            'documentos': qs,
            'q': q,
            'estado': estado,
            'estados': Justificativo._meta.get_field('estado').choices,
        },
    )


@coach
def document_add(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        log(request, f'Cargó justificativo {obj.pk}')
        messages.success(request, 'Justificativo adjuntado correctamente.')
        return redirect('justificativos')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Adjuntar justificativo',
            'ayuda': 'Selecciona una asistencia registrada como ausente o atraso. Al aprobar se marcará Ausente justificado.',
            'cancel_url': reverse('justificativos'),
        },
    )


@login_required
def student_document_add(request):
    if request.user.is_staff:
        return redirect('nuevo_justificativo')
    player = Jugador.objects.filter(rut=request.user.username).first()
    if not player:
        messages.warning(request, 'Tu usuario no está vinculado a un deportista registrado.')
        return redirect('panel_entrenador')
    form = StudentDocumentForm(player, request.POST or None, request.FILES or None)
    if request.method == 'GET' and not form.fields['evaluacion'].queryset.exists():
        messages.info(request, 'No tienes ausencias o atrasos pendientes de justificar.')
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.estado = 'pendiente'
        obj.save()
        log(request, f'Deportista cargó justificativo {obj.pk}')
        messages.success(request, 'Justificativo enviado. Quedó pendiente de revisión por el entrenador.')
        return redirect('panel_entrenador')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Enviar justificativo',
            'ayuda': 'Adjunta un certificado o respaldo en PDF o JPG (hasta 10 MB). El cuerpo técnico lo revisará antes de justificar la inasistencia.',
            'cancel_url': reverse('panel_entrenador'),
        },
    )


@coach
def document_file(request, pk):
    doc = get_object_or_404(Justificativo, pk=pk)
    return FileResponse(doc.archivo.open('rb'), as_attachment=True, filename=f'justificativo-{pk}.{doc.archivo.name.rsplit(".", 1)[-1]}')


@coach
@require_POST
def document_review(request, pk):
    decision = request.POST.get('estado')
    if decision not in ('aprobado', 'rechazado'):
        raise PermissionDenied
    with transaction.atomic():
        doc = get_object_or_404(Justificativo.objects.select_for_update(), pk=pk)
        if doc.estado == 'pendiente':
            doc.estado = decision
            doc.save()
            if decision == 'aprobado':
                Evaluacion.objects.filter(pk=doc.evaluacion_id).update(asistencia='J', nota_frenado=0, nota_pase=0, nota_tiro=0)
            log(request, f'Justificativo {pk}: {decision}')
            messages.success(request, f'Justificativo #{pk} marcado como {decision}.')
    return redirect('justificativos')


@coach
def inventory(request):
    active = {p.equipo_id: p for p in Prestamo.objects.filter(devuelto__isnull=True).select_related('jugador')}
    rows = [(e, active.get(e.pk)) for e in Equipo.objects.order_by('codigo') if not request.GET.get('pendientes') or e.pk in active]
    return render(
        request,
        'seguimiento/inventory.html',
        {'filas': rows, 'prestamos': Prestamo.objects.select_related('jugador', 'equipo').order_by('-fecha')[:100]},
    )


@coach
def equipment_edit(request, pk=None):
    Form = forms.modelform_factory(Equipo, fields=['codigo', 'nombre', 'estado'])
    form = Form(request.POST or None, instance=get_object_or_404(Equipo, pk=pk) if pk else None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        log(request, f'Guardó equipo {obj.pk}')
        messages.success(request, f'Equipo {obj.codigo} guardado correctamente.')
        return redirect('inventario')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Equipamiento del club',
            'cancel_url': reverse('inventario'),
        },
    )


@coach
def loan(request, pk):
    equipment = get_object_or_404(Equipo, pk=pk)
    Form = forms.modelform_factory(Prestamo, fields=['jugador'])
    form = Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if equipment.estado == 'reparacion':
            form.add_error(None, 'Este equipo está en reparación.')
        else:
            try:
                with transaction.atomic():
                    p = form.save(commit=False)
                    p.equipo = equipment
                    p.save()
                    log(request, f'Prestó equipo {pk} al jugador {p.jugador_id}')
                messages.success(request, f'Préstamo de {equipment.nombre} registrado para {p.jugador.nombre_completo}.')
                return redirect('inventario')
            except IntegrityError:
                form.add_error(None, 'Este equipo ya tiene un préstamo pendiente.')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': f'Prestar {equipment}',
            'cancel_url': reverse('inventario'),
        },
    )


@coach
@require_POST
def return_loan(request, pk):
    if Prestamo.objects.filter(pk=pk, devuelto__isnull=True).update(devuelto=timezone.now()):
        log(request, f'Devolvió préstamo {pk}')
        messages.success(request, 'Devolución de equipamiento registrada.')
    return redirect('inventario')


@coach
def routines(request):
    jugador_id = request.GET.get('jugador', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    estado = request.GET.get('estado', '').strip()
    qs = Rutina.objects.select_related('jugador').order_by('completada', '-fecha')
    if jugador_id.isdigit():
        qs = qs.filter(jugador_id=int(jugador_id))
    if categoria:
        qs = qs.filter(jugador__categoria=categoria)
    if estado == 'pendientes':
        qs = qs.filter(completada=False)
    elif estado == 'completadas':
        qs = qs.filter(completada=True)
    return render(
        request,
        'seguimiento/routines.html',
        {
            'rutinas': qs,
            'jugadores': Jugador.objects.order_by('nombre_completo'),
            'categorias': Jugador.CATEGORIAS,
            'jugador_sel': jugador_id,
            'categoria': categoria,
            'estado': estado,
        },
    )


@coach
def routine_edit(request, pk=None):
    Form = forms.modelform_factory(
        Rutina,
        fields=['jugador', 'titulo', 'objetivo', 'ejercicios', 'fecha', 'completada', 'observaciones'],
        widgets={'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')},
    )
    form = Form(request.POST or None, instance=get_object_or_404(Rutina, pk=pk) if pk else None, initial={'fecha': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        log(request, f'Guardó rutina {obj.pk}')
        messages.success(request, f'Rutina "{obj.titulo}" guardada correctamente.')
        return redirect('rutinas')
    return render(
        request,
        'seguimiento/form.html',
        {
            'form': form,
            'titulo': 'Rutina individual',
            'cancel_url': reverse('rutinas'),
        },
    )


@login_required
@require_POST
def student_complete_routine(request, pk):
    player = get_object_or_404(Jugador, rut=request.user.username)
    routine = get_object_or_404(Rutina, pk=pk, jugador=player)
    if not routine.completada:
        routine.completada = True
        routine.save(update_fields=['completada'])
        log(request, f'Deportista completó rutina {routine.pk}')
        messages.success(request, f'Rutina "{routine.titulo}" marcada como completada.')
    return redirect('panel_entrenador')


@coach
def audit_log(request):
    q = request.GET.get('q', '').strip()
    usuario_id = request.GET.get('usuario', '').strip()
    qs = Auditoria.objects.select_related('usuario').order_by('-fecha', '-id')
    if q:
        qs = qs.filter(accion__icontains=q)
    if usuario_id.isdigit():
        qs = qs.filter(usuario_id=int(usuario_id))
    return render(
        request,
        'seguimiento/audit.html',
        {
            'registros': qs[:150],
            'q': q,
            'usuario_sel': usuario_id,
            'usuarios': User.objects.filter(auditoria__isnull=False).distinct().order_by('username'),
        },
    )


def registration_closed(request):
    return render(request, 'seguimiento/registration_closed.html')
