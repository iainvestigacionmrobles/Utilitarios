# 📥 compartir.py — Recibir archivos grandes desde internet

Script Python para recibir archivos de gran tamaño (30 GB o más) desde cualquier persona en internet, sin cuentas, sin contraseñas y sin que tu amigo instale nada.

## ¿Cómo funciona?

1. Tú ejecutas el script desde la carpeta donde quieres recibir el archivo.
2. El script levanta un servidor HTTP local y lo expone a internet mediante un túnel temporal de [Cloudflare](https://www.cloudflare.com/) (gratis, sin cuenta).
3. Te genera una URL única y temporal. Se la mandas a tu amigo por WhatsApp, Telegram, email, etc.
4. Tu amigo abre el enlace en su navegador, selecciona el archivo y lo sube. Ve una barra de progreso.
5. El archivo llega directamente a tu disco, en la carpeta desde donde corriste el script.
6. Cuando termines, presionas `Ctrl+C` y el enlace desaparece.

## Requisitos

- Python 3.x (ya instalado en tu máquina)
- Conexión a internet
- `cloudflared.exe` — **se descarga automáticamente** la primera vez si no lo tienes

## Instalación

No necesitas instalar nada extra. Clona o descarga este repositorio y listo.

```bash
git clone https://github.com/tu-usuario/utilitarios.git
```

## Uso

Abre una terminal, navega a la carpeta donde quieres guardar el archivo y ejecuta el script:

```bash
cd C:\ruta\donde\quieres\guardar
python compartir.py
```

El script detecta automáticamente la carpeta actual y guarda los archivos ahí.

### Ejemplo de salida

```
==============================================================
  RECIBIR ARCHIVOS GRANDES DESDE INTERNET
==============================================================
  Carpeta destino: C:\Users\marco\Descargas
==============================================================
[+] Servidor listo en puerto 8765
[*] Iniciando túnel Cloudflare... (puede tardar 10-20 segundos)

==============================================================
  ✅ ENLACE PARA TU AMIGO:

     https://rabbit-chicago-sunset.trycloudflare.com

  Tu amigo abre ese enlace → selecciona archivo → sube.
  El archivo llega a: C:\Users\marco\Descargas

  Presiona Ctrl+C cuando ya no necesites recibir archivos.
==============================================================
```

## Seguridad

- El enlace es **temporal y aleatorio** — nadie puede adivinarlo.
- **No tiene contraseña**: cualquiera que tenga el enlace puede subir archivos mientras el script esté activo. Ciérralo con `Ctrl+C` al terminar.
- El enlace **deja de funcionar** en cuanto cierras el script.
- El nombre del archivo se sanitiza para evitar ataques de tipo *path traversal*.

## Notas técnicas

- Los archivos se escriben a disco en bloques de 1 MB — no carga el archivo en RAM.
- Compatible con Windows, Linux y macOS (en Linux/Mac cambia `cloudflared.exe` por `cloudflared`).
- Puerto local por defecto: `8765`. Puedes cambiarlo editando la variable `PUERTO` al inicio del script.

## Licencia

MIT — úsalo libremente.
