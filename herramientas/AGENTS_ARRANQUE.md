# AGENTS.md de arranque — Crear proyectos DELSUR con Codex

> Este archivo se guarda como `AGENTS.md` en la carpeta de proyectos del RDP, **`E:\Data`**.
> Cada proyecto vive en su propia subcarpeta, `E:\Data\<NOMBRE>`.
> Los usuarios abren Codex en `E:\Data` para crear un proyecto nuevo, y en `E:\Data\<NOMBRE>`
> para trabajar en él.

Responde siempre en español claro; el usuario no es técnico.

## Guía rápida para el usuario

Codex: si el usuario pregunta cómo empezar o cómo descargar algo a mano, muéstrale esta sección.

**Si no tienes este archivo en `E:\Data`**, descárgalo con PowerShell (no requiere Git ni permisos de administrador):

```powershell
cd "E:\Data"
Invoke-WebRequest "https://raw.githubusercontent.com/DELSURDEV/PlantillaDesarrolloCiudadano/v0.7.0/herramientas/AGENTS_ARRANQUE.md" -OutFile ".\AGENTS.md" -UseBasicParsing
```

**Para crear un proyecto:** abre Codex en `E:\Data` y escribe *"Quiero crear una aplicación nueva."* Codex lo descarga y lo prepara (paso 2 de la sección siguiente).

**Si Codex no puede ejecutar la descarga**, abre PowerShell, copia el bloque del paso 2 de la sección siguiente, cambia `<NOMBRE>` por el nombre del proyecto y ejecútalo. Es el mismo procedimiento: no sobrescribe carpetas existentes ni deja archivos temporales.

Después abre Codex en la carpeta `E:\Data\<NOMBRE>` y escribe: *"Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto."*

## Crear un proyecto nuevo (obligatorio seguir estos pasos)

La **carpeta de proyectos** es `E:\Data`. Cada proyecto se crea en `E:\Data\<NOMBRE>`. No uses otra ruta, ni carpetas temporales de `C:`.

Cuando el usuario pida crear una aplicación o proyecto nuevo:

1. Pide solo el **nombre del proyecto**: letras, números, `-` o `_`, de 3 a 50 caracteres, sin espacios ni tildes (por ejemplo `control-vehiculos`).
2. Ejecuta **exactamente** este bloque en PowerShell, reemplazando solo `<NOMBRE>`. Descarga los archivos de la versión aprobada (ZIP, sin historial ni remoto de Git), no necesita Git ni permisos de administrador y se detiene si la carpeta ya existe:
   ```powershell
   $nombre = "<NOMBRE>"
   $version = "v0.7.0"
   $carpetaProyectos = "E:\Data"
   $ErrorActionPreference = "Stop"
   if ($nombre -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{2,49}$') { throw "Nombre no válido: use letras, números, - o _ (3 a 50, sin espacios)." }
   if (-not (Test-Path -LiteralPath $carpetaProyectos -PathType Container)) { throw "No existe $carpetaProyectos. Contacte a IT." }
   $destino = Join-Path $carpetaProyectos $nombre
   if (Test-Path -LiteralPath $destino) { throw "Ya existe la carpeta $destino. Elija otro nombre." }
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   $temporal = Join-Path $carpetaProyectos (".descarga-" + [guid]::NewGuid().ToString("N"))
   New-Item -ItemType Directory -Path $temporal | Out-Null
   try {
       $zip = Join-Path $temporal "plantilla.zip"
       Invoke-WebRequest "https://github.com/DELSURDEV/PlantillaDesarrolloCiudadano/archive/refs/tags/$version.zip" -OutFile $zip -UseBasicParsing
       Expand-Archive -LiteralPath $zip -DestinationPath $temporal
       $carpeta = Get-ChildItem -LiteralPath $temporal -Directory | Select-Object -First 1
       Move-Item -LiteralPath $carpeta.FullName -Destination $destino
   } finally {
       Remove-Item -LiteralPath $temporal -Recurse -Force -ErrorAction SilentlyContinue
   }
   powershell -ExecutionPolicy Bypass -File (Join-Path $destino "herramientas\preparar_proyecto.ps1")
   ```
   El script de preparación anota la versión en `CONTEXTO_PROYECTO.md`, crea el entorno `.venv`, instala las librerías y corre las pruebas. No toca Git.
3. Si un paso falla, muestra el mensaje al usuario y detente. **No** armes la estructura a mano ni descargues la plantilla por otro medio (tampoco con `git clone`). Si no hay acceso a GitHub o no existe `E:\Data`, pide al usuario que contacte a IT.
4. Al terminar, indica al usuario:
   - Que el inicio de sesión ya está configurado con WAPI_ACCESS (aplicación `/DCIU`): entra con su usuario y contraseña corporativos. Nunca escriba contraseñas en el chat.
   - Que su proyecto quedó en `E:\Data\<NOMBRE>` y que ahí debe guardar todo su trabajo.
   - Que cierre este chat y abra Codex **desde la carpeta del proyecto** `E:\Data\<NOMBRE>` y escriba:
     > Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto.
   - Que para ver la aplicación le pida a Codex, ya en la carpeta del proyecto: *"Abre la aplicación."*
   - Que el chat no se guarda: el avance queda en `CONTEXTO_PROYECTO.md` y en cada sesión nueva basta con escribir *"Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa."*

## Reglas

- Toda aplicación nueva se crea **solo** con la plantilla aprobada; nunca desde cero.
- No conectes los proyectos al repositorio de la plantilla ni subas cambios a él. Si el usuario quiere Git, se usa un repositorio nuevo y propio.
- Nunca borres `.git`, cambies remotos ni reinicies repositorios existentes en `E:\Data`.
- No muevas ni borres proyectos existentes.
- No trabajes proyectos en esta carpeta raíz. Dentro de cada proyecto manda su propio `AGENTS.md`.
