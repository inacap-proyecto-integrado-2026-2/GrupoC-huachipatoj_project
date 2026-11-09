import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage


class SupabaseStorage(Storage):
    """Almacenamiento privado en Supabase Storage (vía REST API, sin dependencias extra)."""

    def __init__(self, base_url=None, service_key=None, bucket=None):
        self.base_url = (base_url or getattr(settings, 'SUPABASE_URL', '')).rstrip('/')
        self.service_key = service_key or getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')
        self.bucket = bucket or getattr(settings, 'SUPABASE_BUCKET', 'huachipato-media')

    def _object_url(self, name, authenticated=False):
        clean_name = name.replace('\\', '/').lstrip('/')
        encoded = urllib.parse.quote(clean_name, safe='/')
        prefix = 'object/authenticated' if authenticated else 'object'
        return f'{self.base_url}/storage/v1/{prefix}/{self.bucket}/{encoded}'

    def _headers(self, extra=None):
        headers = {'apikey': self.service_key}
        if not self.service_key.startswith('sb_'):
            headers['Authorization'] = f'Bearer {self.service_key}'
        if extra:
            headers.update(extra)
        return headers

    def _save(self, name, content):
        clean_name = name.replace('\\', '/').lstrip('/')
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()
        if isinstance(data, str):
            data = data.encode('utf-8')

        content_type = getattr(content, 'content_type', None) or mimetypes.guess_type(clean_name)[0] or 'application/octet-stream'
        req = urllib.request.Request(
            self._object_url(clean_name),
            data=data,
            method='POST',
            headers=self._headers({
                'Content-Type': content_type,
                'x-upsert': 'true',
            }),
        )
        with urllib.request.urlopen(req, timeout=20):
            pass
        return clean_name

    def _open(self, name, mode='rb'):
        req = urllib.request.Request(
            self._object_url(name, authenticated=True),
            method='GET',
            headers=self._headers(),
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return ContentFile(resp.read(), name=name)

    def exists(self, name):
        req = urllib.request.Request(
            self._object_url(name, authenticated=True),
            method='HEAD',
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 404):
                return False
            raise

    def delete(self, name):
        req = urllib.request.Request(
            self._object_url(name),
            method='DELETE',
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.HTTPError as exc:
            if exc.code not in (400, 404):
                raise

    def size(self, name):
        req = urllib.request.Request(
            self._object_url(name, authenticated=True),
            method='HEAD',
            headers=self._headers(),
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return int(resp.headers.get('Content-Length', 0))

    def url(self, name):
        # Los documentos son privados y se descargan únicamente vía vistas protegidas (@coach).
        raise NotImplementedError('Los archivos privados solo pueden descargarse a través de vistas autorizadas.')
