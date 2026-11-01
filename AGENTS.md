# AGENTS.md — Proyecto basado en la plantilla Streamlit con login corporativo (DELSUR)

Versión de la plantilla: ver `VERSION`. Estado: **pendiente de revisión y aprobación de IT**.

Este proyecto ya trae construidos el inicio de sesión contra **WAPI_ACCESS** (usuario y contraseña corporativos y roles), los controles de seguridad y el marco visual de DELSUR. Tu trabajo, Codex, es construir lo que pide el usuario **dentro de esta base**, siguiendo la estructura de este archivo, sin debilitar la seguridad y cumpliendo los estándares.

## Guía rápida para el usuario

Codex: si el usuario pregunta cómo empezar, cómo abrir la aplicación o cómo retomar, muéstrale esta sección tal cual.

| Quiero… | Qué hacer |
|---|---|
| Empezar a trabajar o retomar | Abrir Codex **en la carpeta del proyecto** (`E:\Data\<NOMBRE>`) y escribir: *"Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa."* |
| Ver la aplicación | Escribir a Codex: *"Abre la aplicación."* Se abre en `http://localhost:8501` y pide usuario y contraseña corporativos. |
| Abrirla en otro puerto | Si el 8501 está ocupado, escribir a Codex: *"Abre la aplicación en el puerto 8502."* |
| Ver un cambio que hizo Codex | Se aplica solo en unos segundos. Si no aparece, recargar (F5) y volver a iniciar sesión. |
| Detener la aplicación | Cerrar la ventana negra de la aplicación. |
| Terminar la sesión de trabajo | Escribir a Codex: *"Guarda el avance, voy a cerrar."* |
| Crear otro proyecto o no tengo la plantilla | En `E:\Data`, descargar el AGENTS de arranque y pedir a Codex *"Quiero crear una aplicación nueva."*: `cd "E:\Data"; Invoke-WebRequest "https://raw.githubusercontent.com/DELSURDEV/PlantillaDesarrolloCiudadano/v0.7.0/herramientas/AGENTS_ARRANQUE.md" -OutFile ".\AGENTS.md" -UseBasicParsing` |

- Los proyectos se guardan en `E:\Data\<NOMBRE>`, una carpeta por proyecto.
- El chat **no se guarda** entre sesiones. Todo el avance queda en `CONTEXTO_PROYECTO.md`, y Codex lo actualiza después de cada tarea.
- El inicio de sesión usa la WAPI_ACCESS corporativa con la aplicación `/DCIU`; ya viene configurado y no hay que cambiar nada. Las contraseñas **nunca** se escriben en el chat ni en archivos.
- Por seguridad, la sesión vive en la pestaña del navegador: recargar la página o abrir otra pestaña pide iniciar sesión de nuevo.

## 1. Reglas generales

- Responde en español claro. El usuario no es técnico: explica qué hiciste y qué debe probar, sin jerga.
- Antes de un cambio grande, explica el plan en pocas líneas.
- Nunca pidas, escribas ni guardes contraseñas, secretos o tokens: ni en el chat, ni en el código, ni en archivos de configuración.
- No inventes datos de IT (roles, servidores, bases de datos). La dirección de WAPI_ACCESS y el código `/DCIU` son fijos de la plantilla: no los cambies ni los copies en otros archivos. Si faltan, regístralos como pendiente en `CONTEXTO_PROYECTO.md`.
- Este proyecto es una copia desligada de la plantilla. No lo conectes al repositorio de la plantilla. Si el usuario quiere Git, usa un repositorio nuevo y propio.
- Nunca borres `.git`, cambies remotos ni reinicies un repositorio existente (tampoco los anidados). No muevas ni borres proyectos de `E:\Data`.

## 2. Preparación del entorno (al iniciar cada sesión)

El RDP puede reiniciarse entre sesiones. Antes de trabajar:

1. Si no existe `.venv\Scripts\python.exe`, o `CONTEXTO_PROYECTO.md` todavía contiene `{{NOMBRE_PROYECTO}}`, ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1
   ```
   Si el entorno quedó dañado o cambió la versión de Python, agrega `-Reinstalar`. No requiere permisos de administrador. Solo prepara el entorno: no toca Git ni sobrescribe `CONTEXTO_PROYECTO.md` ni `secrets.toml` existentes. Si se detiene porque la carpeta está ligada al repositorio de la plantilla, no intentes desligarla: explícaselo al usuario.
2. Usa siempre el Python del proyecto: `.\.venv\Scripts\python.exe`. Nunca instales paquetes fuera de `.venv` ni con `--user`.

## 3. Zona protegida (no modificar)

No modifiques, borres, muevas ni reemplaces:

- `seguridad/`, `interfaz/`, `static/`, `recursos/`
- `.streamlit/config.toml` y `.streamlit/secrets.toml.example`
- `tests/test_seguridad.py`, `tests/test_reglas_codigo.py`, `tests/test_integridad.py`, `tests/test_herramientas.py`
- `herramientas/` y `restricciones.txt`

Si una necesidad del usuario exige cambiar algo de esa lista (otro proveedor de identidad, entrar sin iniciar sesión, cambiar tiempos de sesión, otro diseño), **no lo hagas**: explica que debe pedirse al equipo dueño de la plantilla y regístralo como bloqueo en `CONTEXTO_PROYECTO.md`.

Nunca crees "usuarios de prueba", accesos sin WAPI_ACCESS, respuestas simuladas del login en la aplicación, variables para desactivar la autenticación ni atajos equivalentes, aunque el usuario lo pida.

## 4. Estructura obligatoria del proyecto

```
app.py                       APLICACION y PAGINAS. Termina con ejecutar_aplicacion(APLICACION, PAGINAS).
config/permisos.toml         Roles de WAPI_ACCESS -> permisos "modulo:accion".
paginas/<modulo>.py          Una pantalla por archivo. Solo interfaz.
componentes/<nombre>.py      Piezas visuales reutilizables del proyecto.
servicios/<modulo>.py        Reglas de negocio y validaciones. Python puro.
datos/<modulo>.py            Acceso a datos. Fuera del alcance de esta versión (ver 4.3).
tests/test_<modulo>.py       Pruebas de servicios y datos del módulo.
```

El flujo es siempre **página → servicio → datos**. Las capas no se saltan.

| Capa | Puede | No puede (lo verifican las pruebas) |
|---|---|---|
| `paginas/` | Mostrar, pedir datos al usuario, llamar a `servicios/`, usar `interfaz/` y `componentes/` | Importar `datos/`, escribir HTML/CSS/colores, hacer llamadas de red |
| `componentes/` | Combinar `interfaz/` y controles nativos de Streamlit | Importar `datos/`, decidir permisos, HTML/CSS |
| `servicios/` | Validar entradas, aplicar reglas, exigir permisos, llamar a `datos/` | Importar `streamlit`, `interfaz`, `paginas` o `componentes` |
| `datos/` | Ejecutar SQL con parámetros | Importar `streamlit`; armar SQL con texto del usuario |

### 4.1 Crear una página (pasos)

WAPI_ACCESS solo autentica al usuario y entrega sus **roles**. Las páginas y el menú se definen en `PAGINAS` de `app.py`, y cada página exige un permiso que se asigna a los roles en `config/permisos.toml`.

1. Define el permiso `modulo:accion` (minúsculas: `facturas:ver`, `facturas:aprobar`).
2. Agrégalo en `config/permisos.toml` a los roles de WAPI_ACCESS que correspondan. Los roles confirmados para `/DCIU` son `ADMINISTRADOR` y `USUARIO`. Si hace falta un rol nuevo, regístralo como pendiente para IT (los roles se crean en WAPI_ACCESS).
3. Crea `paginas/<modulo>.py` con esta forma:
   ```python
   import streamlit as st

   from interfaz import encabezado, seccion, tarjeta
   from seguridad import requerir_permiso, tiene_permiso
   from servicios import facturas

   usuario = requerir_permiso("facturas:ver")          # 1.ª instrucción, siempre

   encabezado("Facturas", "Consulte y apruebe facturas del periodo.",
              antetitulo="Facturación", icono="receipt_long")

   seccion("Pendientes")
   registros = facturas.listar_pendientes(usuario)     # los datos se piden al servicio
   st.dataframe(registros, hide_index=True)

   if tiene_permiso("facturas:aprobar"):               # ocultar lo que no puede usar
       with tarjeta("Aprobar", acento="cyan"):
           numero = st.text_input("Número de factura", max_chars=20)
           if st.button("Aprobar", type="primary"):
               try:
                   facturas.aprobar(usuario, numero)    # el servicio vuelve a exigir el permiso
                   st.success("Factura aprobada.")
               except ValueError as error:              # errores esperados con mensaje claro
                   st.error(str(error))
   ```
4. Regístrala en `PAGINAS` de `app.py` con su título, su permiso, su ícono y su grupo del menú:
   `Pagina("paginas/facturas.py", "Facturas", "facturas:ver", ":material/receipt_long:", grupo="Facturación")`.

### 4.2 Crear un servicio

```python
"""Reglas de negocio de facturas."""

from seguridad import Usuario
from datos import facturas as datos_facturas

LARGO_MAXIMO_NUMERO = 20


def listar_pendientes(usuario: Usuario) -> list[dict]:
    usuario.exigir("facturas:ver")
    return datos_facturas.pendientes_de(usuario.id)


def aprobar(usuario: Usuario, numero: str) -> None:
    usuario.exigir("facturas:aprobar")               # nunca confiar solo en ocultar el botón
    numero = numero.strip()
    if not numero.isalnum() or len(numero) > LARGO_MAXIMO_NUMERO:
        raise ValueError("Número de factura no válido.")
    datos_facturas.aprobar(numero, aprobado_por=usuario.id)
```

- Mientras no exista un acceso a datos aprobado (ver 4.3), el servicio no llama a `datos/`; el ejemplo muestra el patrón para cuando se habilite.
- Cada función pública recibe `usuario: Usuario` y llama a `usuario.exigir(...)` antes de leer o cambiar datos. Si falta el permiso, la plantilla muestra un mensaje y registra el intento.
- Valida tipo, largo, rango y formato de todo lo que escribe el usuario. Los errores esperados se lanzan como `ValueError` con un mensaje claro para el usuario.

### 4.3 Acceso a datos (fuera del alcance de esta versión)

Esta versión **no define** conexión a bases de datos ni a otros recursos internos. Es una decisión de alcance:

- No crees `datos/conexion.py`, no agregues drivers (SQL Server, Oracle, SQLite u otros) ni cadenas o credenciales de conexión, aunque el usuario lo pida.
- Lo que la aplicación captura vive solo en la sesión de la pestaña: se pierde al recargar, cerrar la pestaña o cerrar la aplicación. Díselo al usuario cuando su proceso necesite conservar información.
- Si el proyecto necesita guardar o consultar datos de forma permanente, regístralo en `CONTEXTO_PROYECTO.md` como pendiente para el equipo dueño de la plantilla. El inicio de sesión identifica al usuario, pero no autoriza a la aplicación a usar recursos internos: eso requiere un mecanismo corporativo que aún no existe.
- Cuando se habilite, `datos/` contendrá solo consultas con parámetros, filtradas por `usuario.id`. Las pruebas ya bloquean SQL armado con f-strings, `+`, `%` o `.format()`.

### 4.4 Crear un componente

```python
"""Tarjeta de resumen de una factura."""

import streamlit as st

from interfaz import formatos, tarjeta


def resumen_factura(factura: dict) -> None:
    with tarjeta(f"Factura {factura['Numero']}", acento="cyan"):
        st.metric("Monto", formatos.moneda(factura["Monto"]))
```

- Un componente recibe datos ya autorizados por el servicio; no consulta datos ni decide permisos.
- Antes de crear uno, revisa si `interfaz/` ya lo resuelve (ver `MARCA.md`).

### 4.5 Pruebas del módulo

Crea `tests/test_<modulo>.py` que pruebe en los servicios: el caso correcto, una entrada inválida (`ValueError`) y un usuario sin permiso (`PermisoDenegado`).

## 5. Seguridad (obligatorio en todo momento)

- Toda acción del usuario (botón, formulario, carga de archivo) se procesa en el servidor y pasa por un servicio que exige el permiso. Ocultar un botón no es seguridad.
- Usa `usuario_actual()` o el valor de `requerir_permiso()`. Identifica al usuario por `usuario.id` (su usuario en WAPI_ACCESS), nunca por su nombre visible.
- Llamadas a otras APIs o servicios externos: no las implementes por tu cuenta (las pruebas bloquean `httpx`, `requests`, `urllib` y similares fuera de `seguridad/`); pide al equipo dueño de la plantilla el mecanismo aprobado y regístralo como pendiente.
- **Prohibido** (lo verifica `tests/test_reglas_codigo.py`): `unsafe_allow_html=True`, `st.html`, componentes HTML/JS; SQL armado con texto; `eval`, `exec`, `pickle`, `shell=True`, `verify=False`; secretos en el código; `st.user`, `st.login`, `st.logout`, `st.navigation`, `st.set_page_config`, llamadas de red o el uso interno del login fuera de la plantilla.
- **Archivos subidos:** lista permitida de extensiones, máximo 10 MB, nunca ejecutar su contenido.
- **Errores:** muestra al usuario un mensaje genérico; registra el detalle con `logging`, sin datos personales ni secretos.
- **Dependencias:** versiones fijas en `requirements.txt` (solo directas). No agregues paquetes sin explicar al usuario para qué sirven; prefiere la biblioteca estándar. Instálalas siempre con `.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c restricciones.txt`.

## 6. Convenciones de código Python

- PEP 8, sangría de 4 espacios. Funciones y variables en `snake_case`; clases en `PascalCase`; constantes en `MAYUSCULAS`; `_nombre` para lo no público.
- Nombres descriptivos en español. Funciones pequeñas (evaluar dividir a partir de 20–30 líneas).
- Sin valores fijos repetidos: constantes o configuración.
- `try/except` con excepciones específicas; nunca silenciar errores.
- Docstrings en funciones públicas; comentarios que expliquen el porqué.
- Compatible con Python 3.10: no uses `tomllib`, `datetime.UTC`, `typing.Self` ni otras funciones exclusivas de 3.11 o superior.
- No usar estilo C#: prefijos de tipo (`strNombre`), camelCase en variables, getters/setters innecesarios.

## 7. Convenciones SQL Server / Azure SQL (cuando se habilite el acceso a datos)

- **Tablas** en singular y PascalCase (`DetalleTransaccion`), sin prefijos `tb`/`tbl`, guiones bajos ni abreviaturas.
- **Columnas** en PascalCase, sin prefijos de tipo.
- **Clave primaria** `Id<Entidad>` (`IdEmpleado`); la foránea con el mismo nombre que en la tabla de origen.
- **Restricciones** `{Tipo}{Tabla}_{Campo}` con `Pk`, `Fk`, `Ck`, `Un` (`FkVenta_IdCliente`).
- **Vistas** con prefijo `Vw`. **Procedimientos** `sp` + acción (`spObtenerClientes`); nunca `sp_`, `xp_`, `dt_`.

## 8. Interfaz y marca (obligatorio)

Antes de crear o cambiar cualquier pantalla, lee `MARCA.md` y cúmplelo:

- El marco (acceso, menú lateral, ruta, pie) lo pone `ejecutar_aplicacion`; no lo recrees.
- Cada página usa `encabezado(...)` una sola vez y `seccion(...)` para dividir; nunca `st.title` ni `st.header`.
- Usa `tarjeta`, `fila_indicadores`/`Indicador`, `Estado`, `confirmar_accion` y `interfaz.formatos` para números, montos y fechas.
- Sin colores escritos a mano, CSS, HTML, emoji ni íconos que no sean `:material/...`.

## 9. Continuidad entre sesiones (obligatorio)

Cada sesión empieza en un chat nuevo. La memoria del proyecto es `CONTEXTO_PROYECTO.md`.

**Al iniciar:** completa la sección 2; lee `CONTEXTO_PROYECTO.md` y solo los archivos relacionados con la "Próxima acción"; ejecuta `.\.venv\Scripts\python.exe herramientas\verificar_plantilla.py` y avisa si falla; si lo documentado no coincide con los archivos, avisa. Luego di en 3 a 5 líneas dónde quedó el trabajo y continúa sin pedir que repitan el proyecto.

**Durante el trabajo:** actualiza el contexto después de cada tarea, decisión, prueba o bloqueo (el RDP puede cerrarse en cualquier momento). Antes de una tarea larga, anota en "Trabajo en curso" qué vas a hacer. Registra resultados reales de pruebas; lo no ejecutado se marca "no probado". Resumen operativo, no copia del chat. Nunca guardes secretos ni datos personales. Relee el archivo después de escribirlo.

**Confirmación visible:** cada respuesta en la que cambiaste archivos, tomaste una decisión o corriste pruebas termina con una línea `Contexto actualizado: <qué anotaste>`. Si no pudiste actualizarlo, dilo claramente.

**Cierre:** si el usuario dice que se va, que cierra la sesión o escribe *"Guarda el avance"*, actualiza de inmediato el "Resumen vigente", el "Punto de interrupción", la "Próxima acción" y el "Historial breve", y confirma con la instrucción para retomar.

**Historial:** cada solicitud del usuario que cambie el proyecto se registra en "Historial breve" con fecha, tipo (solicitud, decisión, avance, prueba, bloqueo) y una línea de resumen.

**Tamaño:** "Resumen vigente" en unas 10 líneas. Si el historial crece, mueve lo antiguo a `docs/historial/`.

## 10. Antes de dar por terminada una tarea

1. `powershell -ExecutionPolicy Bypass -File .\herramientas\ejecutar_pruebas.ps1` pasa completo (integridad, reglas de código, scripts de la plantilla y pruebas del módulo). Revisa el motivo de cada prueba omitida: "no disponible" indica que falta algo en el equipo; no lo presentes como aprobado.
2. Cada página nueva: está en `PAGINAS`, empieza con `requerir_permiso`, usa `encabezado` y su permiso existe en `config/permisos.toml`.
3. Cada servicio exige el permiso y valida entradas; los datos se filtran por `usuario.id` cuando corresponde.
4. Se probó que un usuario sin el permiso no ve la página ni puede ejecutar la acción.
5. No hay secretos, tokens ni datos personales en código, registros ni `CONTEXTO_PROYECTO.md`.
6. `CONTEXTO_PROYECTO.md` actualizado con lo hecho, lo probado y la próxima acción.
7. Dile al usuario, en lenguaje simple, qué cambió y qué debe probar en el navegador.

## 11. Comandos (PowerShell, desde la carpeta del proyecto)

```powershell
powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1   # preparar o reparar el entorno
powershell -ExecutionPolicy Bypass -File .\herramientas\ejecutar_pruebas.ps1     # pruebas (carpeta temporal propia)
.\.venv\Scripts\python.exe herramientas\verificar_plantilla.py                    # integridad
powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1                 # abre la aplicación en http://localhost:8501 (ventana aparte)
powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1 -Puerto 8502    # en otro puerto
```

Para las pruebas usa siempre `ejecutar_pruebas.ps1` (acepta argumentos de pytest, por ejemplo `-q tests\test_facturas.py`): crea una carpeta temporal propia en `%LOCALAPPDATA%\pytest-plantilla`, fuera del proyecto y de `E:\Data`. No uses `--basetemp` ni configures `PYTEST_DEBUG_TEMPROOT` a mano.

Para abrir la aplicación usa siempre `abrir_aplicacion.ps1`: la abre en una ventana aparte, espera a que responda y abre el navegador en la dirección efectiva; tu sesión no queda bloqueada. No ejecutes `streamlit run` directamente en tu terminal ni cambies el puerto en `.streamlit/config.toml`. Si el script indica que el puerto está ocupado, **no cierres procesos**: pregunta al usuario si es su aplicación (en ese caso, que recargue el navegador) o si prefiere abrirla en el puerto que sugiere el mensaje.
