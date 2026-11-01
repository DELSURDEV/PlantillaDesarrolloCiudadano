<#
.SYNOPSIS
  Abre la aplicación del proyecto en una ventana aparte. No requiere permisos de administrador.

  - Usa el puerto 8501, salvo que se indique otro con -Puerto.
  - Si el puerto está ocupado, no cierra ningún programa: explica cómo usar otro puerto.
  - Espera a que la aplicación responda y abre el navegador en la dirección efectiva.
  - El puerto se pasa a Streamlit por línea de comandos (server.port y browser.serverPort),
    sin modificar .streamlit\config.toml ni sus protecciones CORS/XSRF.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1 -Puerto 8502
#>
[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Puerto = 8501,
    # No abre el navegador (por ejemplo, si ya está abierto en esa dirección).
    [switch]$SinNavegador
)

$ErrorActionPreference = "Stop"
$ESPERA_MAXIMA_S = 60

$raiz = Split-Path -Parent $PSScriptRoot
$streamlit = Join-Path $raiz ".venv\Scripts\streamlit.exe"
$direccion = "http://localhost:$Puerto"
$sugerido = if ($Puerto -lt 65535) { $Puerto + 1 } else { $Puerto - 1 }
$otroPuerto = "powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1 -Puerto $sugerido"

function Puerto-Ocupado([int]$numero) {
    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        return [bool](Get-NetTCPConnection -LocalPort $numero -State Listen -ErrorAction SilentlyContinue)
    }
    $cliente = New-Object System.Net.Sockets.TcpClient
    try {
        $cliente.Connect("localhost", $numero)
        return $true
    } catch [System.Net.Sockets.SocketException] {
        return $false
    } finally {
        $cliente.Close()
    }
}

if (-not (Test-Path -LiteralPath $streamlit)) {
    Write-Host "No se encontró el entorno de la aplicación (.venv). Prepare el proyecto con:" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1"
    exit 2
}

if (Puerto-Ocupado $Puerto) {
    Write-Host "El puerto $Puerto ya está en uso: hay otra aplicación abierta (o esta misma)." -ForegroundColor Yellow
    Write-Host "  - Si es esta aplicación, abra $direccion en el navegador y recargue la página."
    Write-Host "  - Si es otra, ciérrela desde su ventana o abra esta en otro puerto:"
    Write-Host "      $otroPuerto"
    Write-Host "No se cerró ningún programa."
    exit 3
}

Write-Host "Abriendo la aplicación en $direccion (se abre una ventana aparte; para detenerla, ciérrela)."
$argumentos = @("run", "app.py", "--server.port", "$Puerto", "--browser.serverPort", "$Puerto")
$proceso = Start-Process -FilePath $streamlit -ArgumentList $argumentos -WorkingDirectory $raiz -PassThru

$limite = (Get-Date).AddSeconds($ESPERA_MAXIMA_S)
while (-not (Puerto-Ocupado $Puerto)) {
    if ($proceso.HasExited) {
        Write-Host "La aplicación se cerró al iniciar. Si el puerto $Puerto quedó ocupado, use otro:" -ForegroundColor Red
        Write-Host "      $otroPuerto"
        exit 4
    }
    if ((Get-Date) -gt $limite) {
        Write-Host "La aplicación no respondió en $ESPERA_MAXIMA_S segundos. Revise los mensajes de su ventana." -ForegroundColor Red
        exit 5
    }
    Start-Sleep -Milliseconds 500
}

Write-Host "Aplicación abierta en $direccion" -ForegroundColor Green
if (-not $SinNavegador) { Start-Process $direccion }
