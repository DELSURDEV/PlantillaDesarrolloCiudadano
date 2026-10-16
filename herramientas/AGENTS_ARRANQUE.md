# AGENTS.md de arranque — Crear proyectos DELSUR con Codex

> Este archivo se guarda como `AGENTS.md` en la carpeta donde se crean los proyectos
> (por ejemplo `D:\Proyectos` en el RDP o `Documentos\Proyectos` en un equipo).
> Los usuarios abren Codex en esa carpeta para crear un proyecto nuevo, y en la carpeta
> del proyecto (`<carpeta de proyectos>\<NOMBRE>`) para trabajar en él.

Responde siempre en español claro; el usuario no es técnico.

## Guía rápida para el usuario

Codex: si el usuario pregunta cómo empezar o cómo descargar algo a mano, muéstrale esta sección.

**Si no tienes este archivo en tu carpeta de proyectos**, descárgalo con PowerShell (no requiere Git ni permisos de administrador):

```powershell
cd "<carpeta de proyectos>"
Invoke-WebRequest "https://raw.githubusercontent.com/DELSURDEV/PlantillaDesarrolloCiudadano/v0.5.2/herramientas/AGENTS_ARRANQUE.md" -OutFile ".\AGENTS.md" -UseBasicParsing
```

**Para crear un proyecto:** abre Codex en la carpeta de proyectos y escribe *"Quiero crear una aplicación nueva."* Codex lo descarga y lo prepara (paso 2 de la sección siguiente).

**Si Codex no puede ejecutar la descarga**, hazla a mano cambiando `<NOMBRE>` por el nombre del proyecto:

```powershell
cd "<carpeta de proyectos>"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest "https://github.com/DELSURDEV/PlantillaDesarrolloCiudadano/archive/refs/tags/v0.5.2.zip" -OutFile ".\plantilla.zip" -UseBasicParsing
Expand-Archive ".\plantilla.zip" -DestinationPath ".\descarga"
Move-Item ".\descarga\PlantillaDesarrolloCiudadano-0.5.2" ".\<NOMBRE>"
Remove-Item ".\plantilla.zip", ".\descarga" -Recurse -Force
powershell -ExecutionPolicy Bypass -File ".\<NOMBRE>\herramientas\preparar_proyecto.ps1"
```

Después abre Codex en la carpeta `<NOMBRE>` y escribe: *"Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto."*

## Crear un proyecto nuevo (obligatorio seguir estos pasos)

La **carpeta de proyectos** es la carpeta donde está este `AGENTS.md` (la carpeta en la que se abrió Codex). No uses otra ruta.

Cuando el usuario pida crear una aplicación o proyecto nuevo:

1. Pide solo el **nombre del proyecto**: letras, números, `-` o `_`, de 3 a 50 caracteres, sin espacios ni tildes (por ejemplo `control-vehiculos`).
2. Ejecuta **exactamente** este bloque en PowerShell, desde la carpeta de proyectos, reemplazando solo `<NOMBRE>`. No necesita Git ni permisos de administrador:
   ```powershell
   $nombre = "<NOMBRE>"
   $version = "v0.5.2"
   $ErrorActionPreference = "Stop"
   if ($nombre -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{2,49}$') { throw "Nombre no válido: use letras, números, - o _ (3 a 50, sin espacios)." }
   $destino = Join-Path (Get-Location) $nombre
   if (Test-Path -LiteralPath $destino) { throw "Ya existe la carpeta $destino. Elija otro nombre." }
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   $temporal = Join-Path (Get-Location) (".descarga-" + [guid]::NewGuid().ToString("N"))
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
   El script de preparación desliga el proyecto de la plantilla, crea el entorno `.venv`, instala las librerías y corre las pruebas.
3. Si un paso falla, muestra el mensaje al usuario y detente. **No** armes la estructura a mano ni descargues la plantilla por otro medio. Si no hay acceso a GitHub, pide al usuario que contacte a IT.
4. Al terminar, indica al usuario:
   - Que complete en `<NOMBRE>\.streamlit\secrets.toml` los datos que entrega IT (client_id, client_secret, TENANT_ID), **sin pegarlos en el chat**.
   - Que cierre este chat y abra Codex **desde la carpeta del proyecto** `<NOMBRE>` y escriba:
     > Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto.
   - Que para ver la aplicación le pida a Codex, ya en la carpeta del proyecto: *"Abre la aplicación."*
   - Que el chat no se guarda: el avance queda en `CONTEXTO_PROYECTO.md` y en cada sesión nueva basta con escribir *"Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa."*

## Reglas

- Toda aplicación nueva se crea **solo** con la plantilla aprobada; nunca desde cero.
- No conectes los proyectos al repositorio de la plantilla ni subas cambios a él. Si el usuario quiere Git, se usa un repositorio nuevo y propio.
- No trabajes proyectos en esta carpeta raíz. Dentro de cada proyecto manda su propio `AGENTS.md`.
