# AGENTS.md de arranque â€” Crear proyectos DELSUR con Codex

> IT coloca este archivo como `D:\Proyectos\AGENTS.md` (y, si lo desea, tambiÃ©n en
> `%USERPROFILE%\.codex\AGENTS.md`). Los usuarios abren Codex en `D:\Proyectos` para crear
> un proyecto nuevo, y en `D:\Proyectos\<NOMBRE>` para trabajar en Ã©l.

Responde siempre en espaÃ±ol claro; el usuario no es tÃ©cnico.

## Crear un proyecto nuevo (obligatorio seguir estos pasos)

Cuando el usuario pida crear una aplicaciÃ³n o proyecto nuevo:

1. Pide solo el **nombre del proyecto**: letras, nÃºmeros, `-` o `_`, de 3 a 50 caracteres, sin espacios ni tildes (por ejemplo `control-vehiculos`).
2. Comprueba que `D:\Proyectos\<NOMBRE>` no exista. Si existe, pide otro nombre.
3. **Descarga** la versiÃ³n aprobada de la plantilla (no la clones para trabajar sobre ella):
   ```powershell
   git -c advice.detachedHead=false clone --depth 1 --branch v0.5.0 https://github.com/DELSURDEV/PlantillaDesarrolloCiudadano.git "D:\Proyectos\<NOMBRE>"
   ```
   Si no hay Git o no hay acceso al repositorio, usa el ZIP aprobado:
   ```powershell
   Expand-Archive -LiteralPath "<RUTA_COMPARTIDA>\plantilla-streamlit-sso-v0.5.0.zip" -DestinationPath "$env:TEMP\plantilla-<NOMBRE>"
   Move-Item "$env:TEMP\plantilla-<NOMBRE>\plantilla-streamlit-sso" "D:\Proyectos\<NOMBRE>"
   ```
4. **Prepara** el proyecto (lo desliga de la plantilla, crea el entorno e instala; no requiere administrador):
   ```powershell
   powershell -ExecutionPolicy Bypass -File "D:\Proyectos\<NOMBRE>\herramientas\preparar_proyecto.ps1"
   ```
5. Si un paso falla, muestra el mensaje al usuario y detente. **No** armes la estructura a mano ni descargues la plantilla por otro medio.
6. Al terminar, indica al usuario:
   - Que complete en `D:\Proyectos\<NOMBRE>\.streamlit\secrets.toml` los datos que entrega IT (client_id, client_secret, TENANT_ID), **sin pegarlos en el chat**.
   - Que cierre este chat y abra Codex **desde** `D:\Proyectos\<NOMBRE>` y escriba:
     > Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayÃºdame a definir el proyecto.

## Reglas

- Toda aplicaciÃ³n nueva se crea **solo** con la plantilla aprobada; nunca desde cero.
- No conectes los proyectos al repositorio de la plantilla ni subas cambios a Ã©l. Si el usuario quiere Git, se usa un repositorio nuevo y propio.
- No trabajes proyectos en esta carpeta raÃ­z. Dentro de cada proyecto manda su propio `AGENTS.md`.


