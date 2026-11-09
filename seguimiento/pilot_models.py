import uuid
from django.db import models
from django.conf import settings
from .models import Jugador, Evaluacion


def document_path(instance, filename):
    return f'justificativos/{uuid.uuid4().hex}.{filename.rsplit(".", 1)[-1].lower()}'


class Justificativo(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.PROTECT)
    archivo = models.FileField(upload_to=document_path)
    motivo = models.CharField(max_length=250)
    estado = models.CharField(max_length=12, default='pendiente', choices=[('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')])
    creado = models.DateTimeField(auto_now_add=True)


class Equipo(models.Model):
    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=[('bueno', 'Bueno'), ('desgastado', 'Desgastado'), ('reparacion', 'En reparación')], default='bueno')

    def __str__(self):
        return f'{self.codigo} · {self.nombre}'


class Prestamo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT)
    jugador = models.ForeignKey(Jugador, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    devuelto = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['equipo'], condition=models.Q(devuelto__isnull=True), name='un_prestamo_activo')]


class Rutina(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=120)
    ejercicios = models.TextField(help_text='Describe ejercicios, repeticiones, duración y descansos.')
    objetivo = models.CharField(max_length=250)
    fecha = models.DateField()
    completada = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)


class Auditoria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=250)
    fecha = models.DateTimeField(auto_now_add=True)


class Autorizacion(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.PROTECT)
    apoderado = models.CharField(max_length=150)
    fecha = models.DateField()
    responsable = models.CharField(max_length=150)
    estado = models.CharField(max_length=12, choices=[('pendiente', 'Pendiente de revisión'), ('vigente', 'Vigente'), ('revocada', 'Revocada')], default='pendiente')
    archivo = models.FileField(upload_to=document_path)
    creado = models.DateTimeField(auto_now_add=True)
