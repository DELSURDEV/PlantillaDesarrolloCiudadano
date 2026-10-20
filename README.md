# Plantilla Streamlit con login corporativo WAPI_ACCESS (DELSUR)

Base estable y controlada para aplicaciones de desarrollo ciudadano construidas con Codex.
Estado: **pendiente de revisión y aprobación de IT**.

Los usuarios **no trabajan sobre este repositorio**: Codex descarga una versión etiquetada siguiendo `herramientas/AGENTS_ARRANQUE.md` y luego `herramientas/preparar_proyecto.ps1` la desliga (borra `.git`), crea el entorno e instala. Si después necesitan control de versiones, crean un repositorio propio.

## Requisitos en el equipo (RDP)

- Windows con **Python 3.10 o superior** (probado con 3.10.0) y acceso a PyPI (directo o por proxy).
- Acceso a github.com (la plantilla se descarga como ZIP de la versión; Git no es necesario).
- **No requiere permisos de administrador**: el entorno virtual `.venv` vive dentro de la carpeta del proyecto, `pip` instala ahí, todas las librerías tienen paquetes precompilados para Windows (no se compila nada) y la app escucha solo en `localhost:8501`. La única condición es que la política de PowerShell permita `-ExecutionPolicy Bypass` para el script, o que IT lo firme.
- Descarga inicial: unos 90 MB de librerías. Si el RDP no tiene acceso a PyPI, IT puede preparar una carpeta con los paquetes (`pip download -r restricciones.txt`) e instalarlos sin internet.

## Librerías

`requirements.txt` tiene solo las dependencias directas; `restricciones.txt` fija la versión exacta de las 52 librerías (directas e indirectas) para Windows y Python 3.10.

| Librería | Versión | Para qué |
|---|---|---|
| streamlit | 1.65.0 | Interfaz (última versión compatible con Python 3.10) |
| httpx | 0.28.1 | Llamada al login de WAPI_ACCESS desde el servidor |
| tzdata | 2026.5 | Zona horaria de El Salvador en Windows |
| tomli | 2.3.0 | Lectura de archivos TOML en Python 3.10 |
| pytest | 9.1.1 | Pruebas |
| Indirectas principales | — | pandas, numpy, pyarrow, altair, starlette, uvicorn (ver `restricciones.txt`) |

## Qué incluye

| Control | Cómo |
|---|---|
| Login corporativo | Usuario y contraseña validados contra `WAPI_ACCESS/api/v2/Auth/login` **desde el servidor** (nunca desde el navegador). No hay secretos ni datos del tenant en el equipo del usuario |
| Datos que se conservan | Solo `userName`, `displayName` y `roles`; la contraseña, los sitemaps y cualquier token de la respuesta se descartan |
| Sesión | En el servidor, ligada a la pestaña (sin cookies). Máximo 8 h (1–12) y 30 min de inactividad (5–60) |
| Intentos fallidos | Bloqueo temporal del usuario tras 5 intentos (3–10) durante 15 min (1–60) |
| Navegación | Las páginas y el menú se definen en `PAGINAS` de `app.py` (título, permiso, ícono y grupo) |
| Autorización | `roles` de WAPI_ACCESS → permisos `modulo:accion` (`config/permisos.toml`); denegado por defecto. Solo se muestran las páginas cuyo permiso tiene el usuario |
| Servicio caído | Si WAPI_ACCESS no responde o responde algo inesperado, nadie entra |
| HTTPS | Obligatorio en producción, salvo excepción registrada (`permitir_http` + `referencia_excepcion_http`) |
| Falla cerrado | Configuración incompleta o insegura → la app no abre |
| Auditoría | Inicios correctos y fallidos, bloqueos, cierres y accesos denegados; nunca contraseñas ni tokens |
| Reglas de código | Pruebas que bloquean HTML sin escapar, SQL concatenado, secretos, llamadas de red fuera de `seguridad/`, etc. |
| Integridad | `herramientas/verificar_plantilla.py` detecta cambios en la zona protegida |
| Marca DELSUR | Marco completo (menú lateral agrupado, ruta, pie institucional), tema, fuentes incluidas, logo oficial y componentes en `interfaz/`; pruebas que bloquean colores, CSS y emoji en las páginas |

## Estructura

```
AGENTS.md            Instrucciones para Codex (estándares y reglas)
MARCA.md             Estándar visual (traducción a Streamlit del sistema de diseño DELSUR)
CONTEXTO_PROYECTO.md Memoria entre sesiones de Codex
app.py               Datos de la aplicación y registro de páginas
paginas/             Pantallas (la plantilla trae solo Inicio)
componentes/         Piezas visuales propias del proyecto
servicios/           Reglas de negocio (Python puro)
datos/               Consultas parametrizadas
seguridad/           Base de seguridad (protegida)
interfaz/            Componentes, formatos y estilos de marca (protegida)
static/fuentes/      Montserrat y Source Sans 3 (licencia OFL, en recursos/licencias)
recursos/            Logos oficiales
config/permisos.toml Roles -> permisos
herramientas/        AGENTS de arranque, preparación del proyecto y verificación de integridad
requirements.txt     Dependencias directas
restricciones.txt    Versiones exactas de todas las dependencias
tests/               Pruebas
```

## Configuración en WAPI_ACCESS (IT)

Todas las aplicaciones de desarrollo ciudadano usan el mismo servicio y código de aplicación, fijos en `seguridad/configuracion.py` (zona protegida):

- URL del login: `http://192.168.132.1/WAPI_ACCESS/api/v2/Auth/login`
- Código de aplicación: `/DCIU`

IT solo debe crear los **roles** en `/DCIU` y asignarlos a los usuarios. Cada proyecto traduce esos roles a permisos en `config/permisos.toml`. Para cambiar la URL o el código, el equipo dueño edita esas dos constantes y publica una versión nueva.

## Publicar una versión (equipo dueño)

```bash
python -m pytest                                   # todo debe pasar
python herramientas/verificar_plantilla.py --generar  # solo si cambió la zona protegida
# actualizar VERSION y la versión (vX.Y.Z) en herramientas/AGENTS_ARRANQUE.md (3 lugares) y en la guía rápida de AGENTS.md
# si cambian dependencias: uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.10 -o restricciones.txt
git commit -am "chore: versión 0.6.2"
git tag v0.6.2 && git push origin main --tags
```

Las copias existentes no reciben cambios automáticamente. Ante una corrección de seguridad, avisar a los dueños de proyectos con la versión afectada (cada proyecto la registra en `CONTEXTO_PROYECTO.md`).

## Mantener la marca al día

El sistema de diseño DELSUR es la fuente oficial; esta plantilla es su traducción a Streamlit. Cuando el sistema cambie, el equipo dueño actualiza `.streamlit/config.toml`, `interfaz/`, `MARCA.md` y publica una versión nueva de la plantilla. Los proyectos no copian el sistema de diseño completo (está pensado para web y React) para que Codex no lo confunda con la arquitectura del proyecto.

## Decisiones pendientes de IT

| Tema | Propuesta |
|---|---|
| HTTPS | Hoy WAPI_ACCESS responde por HTTP: la contraseña viaja sin cifrar por la red interna entre la app y WAPI. Recomendado habilitar HTTPS en WAPI_ACCESS; en producción la plantilla lo exige salvo excepción aprobada. La app también debe publicarse detrás de un proxy con TLS |
| Intentos fallidos | El bloqueo es por usuario y por proceso; confirmar si WAPI_ACCESS ya tiene su propio bloqueo |
| Cambios de rol | Se aplican en el siguiente inicio de sesión (máximo 8 h). Para revocación inmediata, reiniciar la aplicación |
| Varias instancias | La sesión vive en el proceso. Con más de una instancia, usar afinidad de sesión |
| Acceso al repositorio | Repositorio privado con acceso de lectura para los usuarios del RDP, o ZIP en carpeta compartida |
| Arranque de Codex | Colocar `herramientas/AGENTS_ARRANQUE.md` como `D:\Proyectos\AGENTS.md` (y opcionalmente en `%USERPROFILE%\.codex\AGENTS.md`) |
| Python | Confirmar Python 3.10+ en el RDP; recomendado actualizar a una versión 3.10.x reciente (3.10.0 es de 2021) o 3.12 |
| PowerShell | Permitir `-ExecutionPolicy Bypass` para `preparar_proyecto.ps1` o firmarlo |
| Archivos públicos | `static/` se sirve sin inicio de sesión; solo contiene fuentes, logo y supergráfico (lo verifica una prueba) |
| Íconos | Streamlit descarga los íconos Material desde fonts.gstatic.com; permitir ese dominio o aceptar íconos sin imagen |
| Ruta de proyectos | `D:\Proyectos\<NOMBRE>` (confirmar) |
