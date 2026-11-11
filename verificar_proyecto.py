"""Ejecuta comprobaciones y guarda un informe; no modifica datos de la aplicación."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime


def main():
    root = Path(__file__).resolve().parent
    output = root / 'resultados_pruebas'
    output.mkdir(exist_ok=True)
    report = output / ('pruebas-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.txt')
    steps = [
        ['check'],
        ['makemigrations', '--check', '--dry-run'],
        ['test', 'seguimiento', '--verbosity', '2', '--noinput'],
    ]
    failed = False
    with tempfile.TemporaryDirectory(prefix='huachipato-test-') as media, report.open('w', encoding='utf-8') as log:
        env = os.environ.copy()
        env.update(HUACHIPATO_TEST_MEDIA=media, PYTHONIOENCODING='utf-8')
        for args in steps:
            title = '\n>>> ' + ' '.join(args) + '\n'
            print(title, end=''); log.write(title)
            command = [sys.executable, 'manage.py', *args, '--settings=miproyecto.test_settings']
            result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
            print(result.stdout); log.write(result.stdout)
            log.write(f'Código de salida: {result.returncode}\n')
            failed = failed or result.returncode != 0
        summary = 'RESULTADO: REVISAR FALLOS' if failed else 'RESULTADO: COMPROBACIONES SUPERADAS'
        print(summary); log.write('\n' + summary + '\n')
        log.write('Alcance: pruebas automatizadas Django en SQLite. No valida navegador, carga, infraestructura real ni certificación ISO/OWASP.\n')
    print(f'Informe: {report}')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
