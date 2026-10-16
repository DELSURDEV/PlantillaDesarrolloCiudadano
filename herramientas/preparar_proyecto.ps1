<#
.SYNOPSIS
  Prepara un proyecto descargado de la plantilla. No requiere permisos de administrador.

  - Lo desliga del repositorio de la plantilla (borra .git).
  - Registra nombre, versión y fecha en CONTEXTO_PROYECTO.md (solo la primera vez).
  - Crea .streamlit\secrets.toml con una clave de cookie aleatoria (solo si no existe).
  - Crea el entorno virtual .venv dentro del proyecto e instala las librerías fijadas.
  - Verifica la integridad de la plantilla y corre las pruebas.

  Se puede volver a ejecutar sin riesgo (por ejemplo, si el entorno del RDP se reinició).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1
#>
[CmdletBinding()]
param(
    # Borra y vuelve a crear .venv (si se cambió la versión de Python o quedó dañado).
    [switch]$Reinstalar
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
function Paso([string]$texto) { Write-Host "==> $texto" -ForegroundColor Cyan }

$raiz = Split-Path -Parent $PSScriptRoot
$nombre = Split-Path -Leaf $raiz
if ($nombre -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{2,49}$') {
    throw "El nombre de la carpeta '$nombre' no es válido. Use letras, números, '-' o '_' (3 a 50, sin espacios)."
}
$version = "v" + ([IO.File]::ReadAllText((Join-Path $raiz "VERSION"))).Trim()

# 1. Desligar del repositorio de la plantilla
$carpetaGit = Join-Path $raiz ".git"
if (Test-Path -LiteralPath $carpetaGit) {
    Paso "Desligando el proyecto del repositorio de la plantilla"
    Get-ChildItem -LiteralPath $carpetaGit -Recurse -Force | ForEach-Object { $_.Attributes = "Normal" }
    Remove-Item -LiteralPath $carpetaGit -Recurse -Force
}

# 2. CONTEXTO_PROYECTO.md (solo si aún tiene los marcadores de la plantilla)
$contexto = Join-Path $raiz "CONTEXTO_PROYECTO.md"
$texto = [IO.File]::ReadAllText($contexto, $utf8)
if ($texto.Contains("{{NOMBRE_PROYECTO}}")) {
    Paso "Preparando CONTEXTO_PROYECTO.md"
    $texto = $texto.Replace("{{RUTA_PROYECTO}}", $raiz).Replace("{{NOMBRE_PROYECTO}}", $nombre).Replace("{{VERSION_PLANTILLA}}", $version).Replace("{{FECHA}}", (Get-Date -Format "yyyy-MM-dd"))
    [IO.File]::WriteAllText($contexto, $texto, $utf8)
}

# 3. secrets.toml local con clave de cookie aleatoria (nunca se muestra)
$secretos = Join-Path $raiz ".streamlit\secrets.toml"
if (-not (Test-Path -LiteralPath $secretos)) {
    Paso "Creando .streamlit\secrets.toml"
    $bytes = New-Object byte[] 48
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $clave = [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_").TrimEnd("=")
    $ejemplo = [IO.File]::ReadAllText((Join-Path $raiz ".streamlit\secrets.toml.example"), $utf8)
    [IO.File]::WriteAllText($secretos, $ejemplo.Replace("<GENERAR>", $clave), $utf8)
}

# 4. Python 3.10 o superior (lanzador "py" o "python" del usuario; no requiere administrador)
function Buscar-Python {
    foreach ($candidato in @(@("py", "-3"), @("python"))) {
        $comando = Get-Command $candidato[0] -ErrorAction SilentlyContinue
        if (-not $comando) { continue }
        $argumentos = @($candidato | Select-Object -Skip 1)
        & $comando.Source @argumentos -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return ,(@($comando.Source) + $argumentos) }
    }
    throw "No se encontró Python 3.10 o superior. Pida a IT que lo instale."
}

$venv = Join-Path $raiz ".venv"
$pythonVenv = if ($IsLinux -or $IsMacOS) { Join-Path $venv "bin/python" } else { Join-Path $venv "Scripts\python.exe" }
if ($Reinstalar -and (Test-Path -LiteralPath $venv)) {
    Paso "Borrando el entorno virtual anterior"
    Remove-Item -LiteralPath $venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $pythonVenv)) {
    $python = Buscar-Python
    Paso "Creando el entorno virtual .venv"
    $ejecutable = $python[0]
    $argumentos = @($python | Select-Object -Skip 1)
    & $ejecutable @argumentos -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual." }
}

# 5. Librerías (versiones exactas de restricciones.txt)
Paso "Instalando librerías (puede tardar unos minutos la primera vez)"
& $pythonVenv -m pip install --quiet --disable-pip-version-check -r (Join-Path $raiz "requirements.txt") -c (Join-Path $raiz "restricciones.txt")
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar las librerías. Revise la conexión a PyPI o el proxy con IT."
}

# 6. Verificaciones
Paso "Verificando la plantilla"
& $pythonVenv (Join-Path $raiz "herramientas\verificar_plantilla.py")
if ($LASTEXITCODE -ne 0) { throw "La base de seguridad de la plantilla fue modificada." }
Paso "Corriendo las pruebas"
Push-Location $raiz
try {
    & $pythonVenv -m pytest -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw "Hay pruebas que no pasan." }
} finally { Pop-Location }

Write-Host ""
Write-Host "Proyecto '$nombre' listo (plantilla $version, sin relación con su repositorio)." -ForegroundColor Green
Write-Host "Siguientes pasos:"
Write-Host "  1. Complete en .streamlit\secrets.toml: client_id, client_secret y TENANT_ID (datos de IT)."
Write-Host "     No pegue esos valores en el chat."
Write-Host "  2. Para ver la aplicación, pida a Codex: Abre la aplicación."
