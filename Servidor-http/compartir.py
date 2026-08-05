"""
compartir.py - Recibe archivos grandes (30+ GB) desde internet.

Tu amigo abre el enlace en su navegador, selecciona el archivo y lo sube.
El archivo se guarda en la misma carpeta desde donde ejecutas este script.

Requisitos: Python 3
Cloudflared se descarga automaticamente la primera vez.

Uso:
  cd C:\\ruta\\donde\\quieres\\guardar
  python compartir.py
"""

import http.server
import threading
import subprocess
import sys
import os
import urllib.request
import urllib.parse
import re
import time

# ── Configuración ─────────────────────────────────────────────────────────────
# La carpeta destino es siempre donde se ejecuta el script (os.getcwd())
PUERTO          = 8765
CLOUDFLARED_EXE = "cloudflared.exe"
CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
# ──────────────────────────────────────────────────────────────────────────────

HTML_PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Enviar archivo</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; background: #f9f9f9; }
  h2   { color: #222; }
  p    { color: #555; }
  input[type=file] { display: block; margin: 20px 0; font-size: 16px; }
  button { background: #0070f3; color: white; border: none; padding: 12px 28px;
           font-size: 16px; border-radius: 6px; cursor: pointer; }
  button:hover:not(:disabled) { background: #005bb5; }
  button:disabled { background: #aaa; cursor: default; }
  #barra    { width: 100%; background: #ddd; border-radius: 6px; margin-top: 20px; display: none; }
  #progreso { width: 0%; height: 22px; background: #0070f3; border-radius: 6px; transition: width 0.3s; }
  #estado   { margin-top: 12px; font-size: 15px; color: #444; min-height: 22px; }
  #ok       { display: none; color: #007a00; font-size: 18px; font-weight: bold; margin-top: 20px; }
  #error    { display: none; color: #cc0000; font-size: 15px; margin-top: 12px; }
</style>
</head>
<body>
<h2>📤 Enviar archivo</h2>
<p>Selecciona el archivo y presiona <strong>Subir</strong>.<br>
Funciona con archivos muy grandes. No cierres la ventana hasta que termine.</p>

<input type="file" id="archivo">
<button id="btn" onclick="subir()">Subir archivo</button>

<div id="barra"><div id="progreso"></div></div>
<div id="estado"></div>
<div id="ok">✅ Archivo recibido correctamente.</div>
<div id="error"></div>

<script>
function subir() {
  const input  = document.getElementById('archivo');
  if (!input.files.length) { alert('Selecciona un archivo primero.'); return; }

  const archivo = input.files[0];
  const nombre  = encodeURIComponent(archivo.name);
  const btn     = document.getElementById('btn');
  const barra   = document.getElementById('barra');
  const prog    = document.getElementById('progreso');
  const estado  = document.getElementById('estado');
  const errDiv  = document.getElementById('error');

  btn.disabled         = true;
  barra.style.display  = 'block';
  errDiv.style.display = 'none';
  estado.textContent   = 'Iniciando...';

  const xhr = new XMLHttpRequest();
  xhr.open('PUT', '/recibir/' + nombre);

  xhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      const mb  = (e.loaded / 1048576).toFixed(1);
      const tot = (e.total  / 1048576).toFixed(1);
      prog.style.width   = pct + '%';
      estado.textContent = pct + '% — ' + mb + ' MB de ' + tot + ' MB enviados';
    }
  };

  xhr.onload = function() {
    if (xhr.status === 200) {
      prog.style.width = '100%';
      estado.textContent = '';
      document.getElementById('ok').style.display = 'block';
    } else {
      estado.textContent   = '';
      errDiv.style.display = 'block';
      errDiv.textContent   = 'Error del servidor: ' + xhr.responseText;
      btn.disabled = false;
    }
  };

  xhr.onerror = function() {
    estado.textContent   = '';
    errDiv.style.display = 'block';
    errDiv.textContent   = 'Error de conexión. Verifica que el servidor siga activo e intenta de nuevo.';
    btn.disabled = false;
  };

  xhr.send(archivo);
}
</script>
</body>
</html>"""


class RecibirHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGINA.encode("utf-8"))

    def do_PUT(self):
        carpeta_destino = os.getcwd()  # Carpeta desde donde se ejecuta el script

        ruta   = urllib.parse.unquote(self.path)
        nombre = os.path.basename(ruta.replace("/recibir/", ""))
        if not nombre:
            self.send_error(400, "Nombre de archivo vacío")
            return

        # Sanitizar nombre para evitar path traversal
        nombre = os.path.basename(nombre)
        destino = os.path.join(carpeta_destino, nombre)

        tamanio = int(self.headers.get("Content-Length", 0))

        print(f"\n[↓] Recibiendo : {nombre}")
        if tamanio:
            print(f"    Tamaño      : {tamanio / (1024**3):.2f} GB ({tamanio:,} bytes)")
        print(f"    Guardando en: {destino}")

        CHUNK = 1024 * 1024  # 1 MB por lectura
        recibido = 0
        ultimo_pct = -1

        try:
            with open(destino, "wb") as f:
                pendiente = tamanio if tamanio else float("inf")
                while pendiente > 0:
                    bloque = self.rfile.read(min(CHUNK, int(pendiente)))
                    if not bloque:
                        break
                    f.write(bloque)
                    recibido += len(bloque)
                    if tamanio:
                        pendiente -= len(bloque)
                        pct = recibido * 100 // tamanio
                        if pct != ultimo_pct and pct % 5 == 0:
                            ultimo_pct = pct
                            gb = recibido / (1024**3)
                            print(f"    {pct:3d}% — {gb:.2f} GB recibidos", end="\r")

            print(f"\n[✓] Guardado: {destino}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as e:
            print(f"\n[!] Error al guardar: {e}")
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP por defecto


# ── Cloudflared ───────────────────────────────────────────────────────────────

def descargar_cloudflared():
    """Descarga cloudflared.exe junto al script."""
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), CLOUDFLARED_EXE)
    print(f"[*] Descargando cloudflared desde GitHub...")
    try:
        urllib.request.urlretrieve(CLOUDFLARED_URL, destino)
        print(f"[+] Descargado: {destino}")
        return destino
    except Exception as e:
        print(f"[!] Error al descargar cloudflared: {e}")
        print("    Descárgalo manualmente: https://github.com/cloudflare/cloudflared/releases")
        sys.exit(1)


def encontrar_cloudflared():
    """Busca cloudflared en PATH o junto al script; si no existe, lo descarga."""
    import shutil
    ruta = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
    if ruta:
        return ruta
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), CLOUDFLARED_EXE)
    if os.path.isfile(local):
        return local
    return descargar_cloudflared()


def iniciar_tunel(exe):
    """Lanza cloudflared tunnel y devuelve (proceso, url_publica)."""
    cmd = [exe, "tunnel", "--url", f"http://127.0.0.1:{PUERTO}"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    patron = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    print("[*] Iniciando túnel Cloudflare... (puede tardar 10-20 segundos)")
    for linea in proc.stdout:
        m = patron.search(linea)
        if m:
            return proc, m.group(0)
    return proc, None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    carpeta_actual = os.getcwd()

    print("=" * 62)
    print("  RECIBIR ARCHIVOS GRANDES DESDE INTERNET")
    print("=" * 62)
    print(f"  Carpeta destino: {carpeta_actual}")
    print("=" * 62)

    # Servidor HTTP
    servidor = http.server.HTTPServer(("127.0.0.1", PUERTO), RecibirHandler)
    t = threading.Thread(target=servidor.serve_forever, daemon=True)
    t.start()
    print(f"[+] Servidor listo en puerto {PUERTO}")

    # Túnel
    cf_exe = encontrar_cloudflared()
    proc_cf, url = iniciar_tunel(cf_exe)

    if not url:
        print("[!] No se pudo obtener la URL pública de cloudflared.")
        servidor.shutdown()
        sys.exit(1)

    print()
    print("=" * 62)
    print("  ✅ ENLACE PARA TU AMIGO:")
    print()
    print(f"     {url}")
    print()
    print("  Tu amigo abre ese enlace → selecciona archivo → sube.")
    print(f"  El archivo llega a: {carpeta_actual}")
    print()
    print("  Presiona Ctrl+C cuando ya no necesites recibir archivos.")
    print("=" * 62)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Cerrando servidor...")
        proc_cf.terminate()
        servidor.shutdown()
        print("[+] Listo. El enlace ya no es accesible.")


if __name__ == "__main__":
    main()
