from django.contrib import admin
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Justificativo, Equipo, Prestamo, Rutina, Auditoria, Autorizacion


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'categoria', 'fecha_nacimiento', 'contacto_emergencia')
    list_filter = ('categoria',)
    search_fields = ('nombre_completo', 'rut')


@admin.register(ClaseEntrenamiento)
class ClaseEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'hora', 'categoria', 'estado', 'profesor')
    list_filter = ('estado', 'categoria', 'fecha')
    search_fields = ('profesor', 'objetivo')


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'clase', 'asistencia', 'nota_frenado', 'nota_pase', 'nota_tiro')
    list_filter = ('asistencia', 'categoria_registrada')
    search_fields = ('jugador__nombre_completo', 'jugador__rut')


@admin.register(Justificativo)
class JustificativoAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'estado', 'revisado_por', 'creado')
    list_filter = ('estado',)
    search_fields = ('evaluacion__jugador__nombre_completo', 'motivo')


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre')


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'jugador', 'fecha', 'devuelto')
    search_fields = ('equipo__codigo', 'jugador__nombre_completo')


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'jugador', 'fecha', 'completada')
    list_filter = ('completada', 'fecha')
    search_fields = ('titulo', 'jugador__nombre_completo')


@admin.register(Autorizacion)
class AutorizacionAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'apoderado', 'estado', 'fecha', 'responsable')
    list_filter = ('estado',)
    search_fields = ('jugador__nombre_completo', 'apoderado')


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion')
    search_fields = ('accion', 'usuario__username')
