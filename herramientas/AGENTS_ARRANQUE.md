# AGENTS.md de arranque — Crear proyectos DELSUR con Codex

> Este archivo se guarda como `AGENTS.md` en la raíz del disco de proyectos del RDP, **`E:\`** (el disco cuya etiqueta es "Data"; `Data` no es una carpeta).
> Cada usuario tiene su carpeta y, dentro de ella, una carpeta por proyecto: `E:\<USUARIO>\<NOMBRE>`.
> Los usuarios abren Codex en `E:\` para crear un proyecto nuevo, y en `E:\<USUARIO>\<NOMBRE>`
> para trabajar en él.

Responde siempre en español claro; el usuario no es técnico.

## Guía rápida para el usuario

Codex: si el usuario pregunta cómo empezar o cómo descargar algo a mano, muéstrale esta sección.

**Si no tienes este archivo en `E:\`**, descárgalo con PowerShell (no requiere Git ni permisos de administrador):

```powershell
cd "E:\"
Invoke-WebRequest "https://raw.githubusercontent.com/DELSURDEV/PlantillaDesarrolloCiudadano/v0.7.1/herramientas/AGENTS_ARRANQUE.md" -OutFile ".\AGENTS.md" -UseBasicParsing
```

**Para crear un proyecto:** abre Codex en `E:\` y escribe *"Quiero crear una aplicación nueva."* Codex confirma tu usuario, pide el nombre del proyecto, lo descarga y lo prepara (paso 3 de la sección siguiente).

**Si Codex no puede ejecutar la descarga**, abre PowerShell, copia el bloque del paso 3 de la sección siguiente, cambia `<USUARIO>` por tu usuario y `<NOMBRE>` por el nombre del proyecto, y ejecútalo. Es el mismo procedimiento: no sobrescribe carpetas existentes ni deja archivos temporales.

Después abre Codex en la carpeta `E:\<USUARIO>\<NOMBRE>` y escribe: *"Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto."*

## Crear un proyecto nuevo (obligatorio seguir estos pasos)

El **disco de proyectos** es `E:\`. Cada proyecto se crea en `E:\<USUARIO>\<NOMBRE>`. No uses otra ruta, ni carpetas temporales de `C:`.

Cuando el usuario pida crear una aplicación o proyecto nuevo:

1. **Confirma el usuario.** Consulta el usuario de Windows con `$env:USERNAME` y pregunta: *"¿Tu usuario es `<usuario de Windows>`? Tus proyectos quedarán en `E:\<usuario de Windows>`."* Espera la respuesta. Si dice que no, o el valor está vacío, pídele que lo escriba: letras, números, `.`, `-` o `_`, sin espacios ni tildes. Es solo el nombre de la carpeta: nunca pidas su contraseña. Si `E:\<USUARIO>` ya existe, los proyectos nuevos se crean ahí dentro, sin tocar los que ya estén.
2. Pide el **nombre del proyecto**: letras, números, `-` o `_`, de 3 a 50 caracteres, sin espacios ni tildes (por ejemplo `GTMP`).
3. Ejecuta **exactamente** este bloque en PowerShell, reemplazando solo `<USUARIO>` y `<NOMBRE>`. Descarga los archivos de la versión aprobada (ZIP, sin historial ni remoto de Git), no necesita Git ni permisos de administrador, reutiliza la carpeta del usuario si ya existe y se detiene si el proyecto ya existe:
   ```powershell
   $usuario = "<USUARIO>"
   $nombre = "<NOMBRE>"
   $version = "v0.7.1"
   $disco = "E:\"
   $ErrorActionPreference = "Stop"
   $reservados = '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$'
   if ($usuario -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,48}[A-Za-z0-9_-]$' -or $usuario -match $reservados) { throw "Usuario no válido: use letras, números, '.', '-' o '_' (2 a 50, sin espacios)." }
   if ($nombre -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{2,49}$' -or $nombre -match $reservados) { throw "Nombre no válido: use letras, números, - o _ (3 a 50, sin espacios)." }
   if (-not (Test-Path -LiteralPath $disco -PathType Container)) { throw "No existe el disco $disco. Contacte a IT." }
   $carpetaUsuario = Join-Path $disco $usuario
   if (Test-Path -LiteralPath $carpetaUsuario -PathType Leaf) { throw "$carpetaUsuario es un archivo, no una carpeta. Contacte a IT." }
   $destino = Join-Path $carpetaUsuario $nombre
   if (Test-Path -LiteralPath $destino) { throw "Ya existe $destino. Elija otro nombre de proyecto." }
   New-Item -ItemType Directory -Force -Path $carpetaUsuario | Out-Null
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   $temporal = Join-Path $carpetaUsuario (".descarga-" + [guid]::NewGuid().ToString("N"))
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
4. Si un paso falla, muestra el mensaje al usuario y detente. **No** armes la estructura a mano ni descargues la plantilla por otro medio (tampoco con `git clone`). Si no hay acceso a GitHub, no existe el disco `E:\` o no se puede crear la carpeta, pide al usuario que contacte a IT.
5. Al terminar, indica al usuario:
   - Que el inicio de sesión ya está configurado con WAPI_ACCESS (aplicación `/DCIU`): entra con su usuario y contraseña corporativos. Nunca escriba contraseñas en el chat.
   - Que su proyecto quedó en `E:\<USUARIO>\<NOMBRE>` y que ahí debe guardar todo su trabajo.
   - Que cierre este chat y abra Codex **desde la carpeta del proyecto** `E:\<USUARIO>\<NOMBRE>` y escriba:
     > Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto.
   - Que para ver la aplicación le pida a Codex, ya en la carpeta del proyecto: *"Abre la aplicación."*
   - Que el chat no se guarda: el avance queda en `CONTEXTO_PROYECTO.md` y en cada sesión nueva basta con escribir *"Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa."*

## Reglas

- Toda aplicación nueva se crea **solo** con la plantilla aprobada; nunca desde cero.
- No conectes los proyectos al repositorio de la plantilla ni subas cambios a él. Si el usuario quiere Git, se usa un repositorio nuevo y propio.
- Crea proyectos solo en la carpeta del usuario confirmado. No entres ni cambies carpetas de otros usuarios.
- Nunca borres `.git`, cambies remotos ni reinicies repositorios existentes en `E:\`.
- No muevas ni borres proyectos existentes.
- No trabajes proyectos en la raíz de `E:\` ni directamente en la carpeta del usuario. Dentro de cada proyecto manda su propio `AGENTS.md`.
