<#
.SYNOPSIS
  Ejecuta las pruebas del proyecto con una carpeta temporal propia. No requiere permisos de administrador.

  - Crea una subcarpeta única por ejecución en %LOCALAPPDATA%\pytest-plantilla y se la indica a pytest
    con PYTEST_DEBUG_TEMPROOT, solo en este proceso; al terminar restaura el valor anterior.
  - Nunca usa el proyecto ni el disco E: como carpeta temporal, y rechaza --basetemp (en argumentos,
    PYTEST_ADDOPTS o archivos de configuración de pytest), porque pytest vacía esa carpeta.
  - Si las pruebas pasan, borra solo su propia subcarpeta; si fallan, la conserva para revisarla.
  - Muestra el motivo de cada prueba omitida (-rs). Devuelve el código de salida de pytest.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\herramientas\ejecutar_pruebas.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\herramientas\ejecutar_pruebas.ps1 -q tests\test_facturas.py
#>
# Sin bloque param: los argumentos para pytest (por ejemplo -q) llegan completos en $args.

$ErrorActionPreference = "Stop"
$DISCO_PROYECTOS = "E:\"
$VARIABLE_TEMPORAL = "PYTEST_DEBUG_TEMPROOT"
$PATRON_EJECUCION = '^ejecucion-[0-9a-f]{8}$'
$CODIGO_RECHAZO = 2

$raiz = Split-Path -Parent $PSScriptRoot
$python = Join-Path $raiz ".venv\Scripts\python.exe"
$argumentos = @($args)

function Detener([string]$mensaje) {
    Write-Host $mensaje -ForegroundColor Red
    exit $CODIGO_RECHAZO
}

function Esta-Dentro([string]$ruta, [string]$carpeta) {
    $ruta = $ruta.TrimEnd("\")
    $carpeta = $carpeta.TrimEnd("\")
    return $ruta.Equals($carpeta, [StringComparison]::OrdinalIgnoreCase) -or
        $ruta.StartsWith($carpeta + "\", [StringComparison]::OrdinalIgnoreCase)
}

if (-not (Test-Path -LiteralPath $python)) {
    Detener ("No se encontró el entorno .venv. Prepare el proyecto con: " +
        "powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1")
}

# --basetemp haría que pytest vacíe una carpeta elegida fuera de este mecanismo.
# pytest no acepta abreviaturas de opciones, así que basta con buscar el nombre completo.
if (@($argumentos) + @("$env:PYTEST_ADDOPTS") | Where-Object { "$_" -match '--basetemp' }) {
    Detener "No se permite --basetemp: la carpeta temporal de las pruebas la define este script."
}
foreach ($archivo in @("pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")) {
    $ruta = Join-Path $raiz $archivo
    if ((Test-Path -LiteralPath $ruta) -and ([IO.File]::ReadAllText($ruta) -match 'basetemp')) {
        Detener "No se permite basetemp en ${archivo}: la carpeta temporal de las pruebas la define este script."
    }
}

$local = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($local)) { $local = [IO.Path]::GetTempPath() }
# [IO.Path]::Combine no exige que la unidad exista (Join-Path sí), así se valida antes de crear nada.
$base = [IO.Path]::GetFullPath([IO.Path]::Combine($local, "pytest-plantilla"))
if ((Esta-Dentro $base $raiz) -or (Esta-Dentro $base $DISCO_PROYECTOS)) {
    Detener "La carpeta temporal $base queda dentro del proyecto o del disco $DISCO_PROYECTOS. Revise LOCALAPPDATA con IT."
}

New-Item -ItemType Directory -Force -Path $base | Out-Null
$nombre = "ejecucion-" + [guid]::NewGuid().ToString("N").Substring(0, 8)
$carpeta = Join-Path $base $nombre
New-Item -ItemType Directory -Path $carpeta | Out-Null
Write-Host "Carpeta temporal de pruebas: $carpeta"

$anterior = [Environment]::GetEnvironmentVariable($VARIABLE_TEMPORAL, "Process")
[Environment]::SetEnvironmentVariable($VARIABLE_TEMPORAL, $carpeta, "Process")
Push-Location -LiteralPath $raiz
try {
    & $python -m pytest -p no:cacheprovider -rs @argumentos
    $codigo = $LASTEXITCODE
} finally {
    Pop-Location
    [Environment]::SetEnvironmentVariable($VARIABLE_TEMPORAL, $anterior, "Process")
}

if ($codigo -ne 0) {
    Write-Host "Las pruebas no pasaron. Se conserva la carpeta temporal para revisarla: $carpeta"
    exit $codigo
}

# Solo se borra la subcarpeta creada por esta ejecución. rmdir /s no sigue los enlaces (junctions):
# borra el enlace, nunca el contenido de su destino.
$actual = Get-Item -LiteralPath $carpeta -Force
$esPropia = ($actual.FullName.TrimEnd("\") -ieq $carpeta.TrimEnd("\")) -and
    ($actual.Parent.FullName.TrimEnd("\") -ieq $base.TrimEnd("\")) -and
    ($actual.Name -match $PATRON_EJECUCION) -and
    -not ($actual.Attributes -band [IO.FileAttributes]::ReparsePoint)
if (-not $esPropia) {
    Write-Warning "No se borró la carpeta temporal $carpeta porque no coincide con la creada por esta ejecución."
    exit $codigo
}
& cmd.exe /d /c rmdir /s /q $carpeta
if (Test-Path -LiteralPath $carpeta) {
    Write-Warning "No se pudo borrar por completo la carpeta temporal $carpeta. Puede borrarla después."
}
exit $codigo
