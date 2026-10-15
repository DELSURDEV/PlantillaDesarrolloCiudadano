# Plantilla Streamlit con SSO de Microsoft (DELSUR)

Base estable y controlada para aplicaciones de desarrollo ciudadano construidas con Codex.
Estado: **pendiente de revisión y aprobación de IT**.

Los usuarios **no trabajan sobre este repositorio**: Codex descarga una versión etiquetada siguiendo `herramientas/AGENTS_ARRANQUE.md` y luego `herramientas/preparar_proyecto.ps1` la desliga (borra `.git`), crea el entorno e instala. Si después necesitan control de versiones, crean un repositorio propio.

## Requisitos en el equipo (RDP)

- Windows con **Python 3.10 o superior** (probado con 3.10.0) y acceso a PyPI (directo o por proxy).
- Git (opcional; sin Git se usa el ZIP de la versión).
- **No requiere permisos de administrador**: el entorno virtual `.venv` vive dentro de la carpeta del proyecto, `pip` instala ahí, todas las librerías tienen paquetes precompilados para Windows (no se compila nada) y la app escucha solo en `localhost:8501`. La única condición es que la política de PowerShell permita `-ExecutionPolicy Bypass` para el script, o que IT lo firme.
- Descarga inicial: unos 90 MB de librerías. Si el RDP no tiene acceso a PyPI, IT puede preparar una carpeta con los paquetes (`pip download -r restricciones.txt`) e instalarlos sin internet.

## Librerías

`requirements.txt` tiene solo las dependencias directas; `restricciones.txt` fija la versión exacta de las 52 librerías (directas e indirectas) para Windows y Python 3.10.

| Librería | Versión | Para qué |
|---|---|---|
| streamlit[auth] | 1.65.0 | Interfaz e inicio de sesión OIDC (última versión compatible con Python 3.10) |
| authlib | 1.9.1 | Flujo OIDC con Entra ID (validación del ID token) |
| tzdata | 2026.5 | Zona horaria de El Salvador en Windows |
| tomli | 2.3.0 | Lectura de archivos TOML en Python 3.10 |
| pytest | 9.1.1 | Pruebas |
| Indirectas principales | — | pandas, numpy, pyarrow, altair, starlette, uvicorn, httpx, cryptography, joserfc (ver `restricciones.txt`) |

## Qué incluye

| Control | Cómo |
|---|---|
| SSO Microsoft Entra ID (OIDC, código + PKCE) | `st.login()` de Streamlit con tenant único (no `common`) |
| Validación de identidad | Tenant, emisor, audiencia, `oid` en cada ejecución |
| Duración máxima de sesión | 8 h desde el inicio de sesión (configurable 1–12 h) |
| Inactividad | 30 min (configurable 5–60), compartida entre pestañas |
| Autorización | App roles de Entra → permisos `modulo:accion`; denegado por defecto |
| Páginas | Solo se muestran las permitidas; cada página exige su permiso |
| Falla cerrado | Configuración incompleta o insegura → la app no abre |
| Auditoría | Inicio/cierre de sesión y accesos denegados, sin tokens ni correos |
| Reglas de código | Pruebas que bloquean HTML sin escapar, SQL concatenado, secretos, etc. |
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

## Registro en Entra ID (IT)

1. **Registro de aplicación**, un solo tenant.
2. **Autenticación → plataforma Web** (no SPA) con la URI de redirección exacta:
   - Desarrollo: `http://localhost:8501/oauth2callback`
   - Producción: `https://<host>/oauth2callback`
   
   Streamlit usa la misma URI como destino después de cerrar sesión.
3. **Certificados y secretos**: secreto de cliente (Streamlit no admite certificado; ver decisiones pendientes).
4. **Roles de aplicación**: `Usuario` y `Administrador` (valor exacto), tipo "Usuarios/Grupos".
5. **Aplicación empresarial → Propiedades**: "¿Se requiere asignación?" = **Sí**. Asignar usuarios o grupos a los roles.
6. Entregar al usuario: tenant ID, client ID y el secreto por un canal seguro (no por chat ni correo).

## Publicar una versión (equipo dueño)

```bash
python -m pytest                                   # todo debe pasar
python herramientas/verificar_plantilla.py --generar  # solo si cambió la zona protegida
# actualizar VERSION y la etiqueta en herramientas/AGENTS_ARRANQUE.md
# si cambian dependencias: uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.10 -o restricciones.txt
git commit -am "chore: versión 0.5.0"
git tag v0.5.0 && git push origin main --tags
```

Las copias existentes no reciben cambios automáticamente. Ante una corrección de seguridad, avisar a los dueños de proyectos con la versión afectada (cada proyecto la registra en `CONTEXTO_PROYECTO.md`).

## Mantener la marca al día

El sistema de diseño DELSUR es la fuente oficial; esta plantilla es su traducción a Streamlit. Cuando el sistema cambie, el equipo dueño actualiza `.streamlit/config.toml`, `interfaz/`, `MARCA.md` y publica una versión nueva de la plantilla. Los proyectos no copian el sistema de diseño completo (está pensado para web y React) para que Codex no lo confunda con la arquitectura del proyecto.

## Decisiones pendientes de IT

| Tema | Propuesta |
|---|---|
| Secreto de cliente vs. certificado | Streamlit solo admite secreto. Aceptar como excepción, con rotación máxima de 6 meses y guardado en un gestor de secretos en producción |
| HTTPS y cabeceras | Producción detrás de un proxy (IIS, Application Gateway) con TLS, HSTS, `X-Frame-Options: DENY` y CSP. La cookie de sesión de Streamlit no tiene `Secure`; el proxy debe forzar HTTPS |
| Cambios de rol | Se aplican en el siguiente inicio de sesión (máximo 8 h). Para revocación inmediata, deshabilitar al usuario en Entra y reiniciar la app |
| Varias instancias | El control de inactividad es por proceso. Con más de una instancia, usar afinidad de sesión |
| Acceso al repositorio | Repositorio privado con acceso de lectura para los usuarios del RDP, o ZIP en carpeta compartida |
| Arranque de Codex | Colocar `herramientas/AGENTS_ARRANQUE.md` como `D:\Proyectos\AGENTS.md` (y opcionalmente en `%USERPROFILE%\.codex\AGENTS.md`) |
| Python | Confirmar Python 3.10+ en el RDP; recomendado actualizar a una versión 3.10.x reciente (3.10.0 es de 2021) o 3.12 |
| PowerShell | Permitir `-ExecutionPolicy Bypass` para `preparar_proyecto.ps1` o firmarlo |
| Archivos públicos | `static/` se sirve sin inicio de sesión; solo contiene fuentes, logo y supergráfico (lo verifica una prueba) |
| Íconos | Streamlit descarga los íconos Material desde fonts.gstatic.com; permitir ese dominio o aceptar íconos sin imagen |
| Ruta de proyectos | `D:\Proyectos\<NOMBRE>` (confirmar) |
