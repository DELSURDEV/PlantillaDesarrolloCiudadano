# AGENTS.md — Proyecto basado en la plantilla Streamlit con SSO (DELSUR)

Versión de la plantilla: ver `VERSION`. Estado: **pendiente de revisión y aprobación de IT**.

Este proyecto ya trae construidos el inicio de sesión con Microsoft Entra ID, los controles de seguridad y el marco visual de DELSUR. Tu trabajo, Codex, es construir lo que pide el usuario **dentro de esta base**, siguiendo la estructura de este archivo, sin debilitar la seguridad y cumpliendo los estándares.

## 1. Reglas generales

- Responde en español claro. El usuario no es técnico: explica qué hiciste y qué debe probar, sin jerga.
- Antes de un cambio grande, explica el plan en pocas líneas.
- Nunca pidas que se peguen en el chat contraseñas, secretos, tokens ni el contenido de `.streamlit/secrets.toml`. El `client_id` y el `tenant_id` no son secretos.
- No inventes datos de IT (tenant, client ID, roles, servidores, bases de datos). Si faltan, regístralos como pendiente en `CONTEXTO_PROYECTO.md`.
- Este proyecto es una copia desligada de la plantilla. No lo conectes al repositorio de la plantilla. Si el usuario quiere Git, usa un repositorio nuevo y propio.

## 2. Preparación del entorno (al iniciar cada sesión)

El RDP puede reiniciarse entre sesiones. Antes de trabajar:

1. Si no existe `.venv\Scripts\python.exe`, o `CONTEXTO_PROYECTO.md` todavía contiene `{{NOMBRE_PROYECTO}}`, ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1
   ```
   Si el entorno quedó dañado o cambió la versión de Python, agrega `-Reinstalar`. No requiere permisos de administrador.
2. Usa siempre el Python del proyecto: `.\.venv\Scripts\python.exe`. Nunca instales paquetes fuera de `.venv` ni con `--user`.

## 3. Zona protegida (no modificar)

No modifiques, borres, muevas ni reemplaces:

- `seguridad/`, `interfaz/`, `static/`, `recursos/`
- `.streamlit/config.toml` y `.streamlit/secrets.toml.example`
- `tests/test_seguridad.py`, `tests/test_reglas_codigo.py`, `tests/test_integridad.py`
- `herramientas/` y `restricciones.txt`

Si una necesidad del usuario exige cambiar algo de esa lista (otro proveedor de identidad, entrar sin iniciar sesión, cambiar tiempos de sesión, otro diseño), **no lo hagas**: explica que debe pedirse al equipo dueño de la plantilla y regístralo como bloqueo en `CONTEXTO_PROYECTO.md`.

Nunca crees "usuarios de prueba", accesos sin Microsoft, variables para desactivar la autenticación ni atajos equivalentes, aunque el usuario lo pida.

## 4. Estructura obligatoria del proyecto

```
app.py                       APLICACION y PAGINAS. Termina con ejecutar_aplicacion(APLICACION, PAGINAS).
config/permisos.toml         Roles de Entra ID -> permisos "modulo:accion".
paginas/<modulo>.py          Una pantalla por archivo. Solo interfaz.
componentes/<nombre>.py      Piezas visuales reutilizables del proyecto.
servicios/<modulo>.py        Reglas de negocio y validaciones. Python puro.
datos/<modulo>.py            Consultas a la base de datos. Solo SQL parametrizado.
datos/conexion.py            Conexión (se crea cuando haya base de datos; credenciales en secrets.toml).
tests/test_<modulo>.py       Pruebas de servicios y datos del módulo.
```

El flujo es siempre **página → servicio → datos**. Las capas no se saltan.

| Capa | Puede | No puede (lo verifican las pruebas) |
|---|---|---|
| `paginas/` | Mostrar, pedir datos al usuario, llamar a `servicios/`, usar `interfaz/` y `componentes/` | Importar `datos/`, escribir HTML/CSS/colores, usar `st.user`/`st.login` |
| `componentes/` | Combinar `interfaz/` y controles nativos de Streamlit | Importar `datos/`, decidir permisos, HTML/CSS |
| `servicios/` | Validar entradas, aplicar reglas, exigir permisos, llamar a `datos/` | Importar `streamlit`, `interfaz`, `paginas` o `componentes` |
| `datos/` | Ejecutar SQL con parámetros | Importar `streamlit`; armar SQL con texto del usuario |

### 4.1 Crear una página (pasos)

1. Define el permiso `modulo:accion` (minúsculas: `facturas:ver`, `facturas:aprobar`).
2. Agrégalo en `config/permisos.toml` a los roles que correspondan. Si hace falta un rol nuevo, regístralo como pendiente para IT (los roles se crean en Entra ID).
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
4. Regístrala en `PAGINAS` de `app.py` con su grupo del menú:
   `Pagina("paginas/facturas.py", "Facturas", "facturas:ver", ":material/receipt_long:", grupo="Facturación")`.

### 4.2 Crear un servicio

```python
"""Reglas de negocio de facturas."""

from seguridad import Usuario
from datos import facturas as datos_facturas

LARGO_MAXIMO_NUMERO = 20


def listar_pendientes(usuario: Usuario) -> list[dict]:
    usuario.exigir("facturas:ver")
    return datos_facturas.pendientes_de(usuario.oid)


def aprobar(usuario: Usuario, numero: str) -> None:
    usuario.exigir("facturas:aprobar")               # nunca confiar solo en ocultar el botón
    numero = numero.strip()
    if not numero.isalnum() or len(numero) > LARGO_MAXIMO_NUMERO:
        raise ValueError("Número de factura no válido.")
    datos_facturas.aprobar(numero, aprobado_por=usuario.oid)
```

- Cada función pública recibe `usuario: Usuario` y llama a `usuario.exigir(...)` antes de leer o cambiar datos. Si falta el permiso, la plantilla muestra un mensaje y registra el intento.
- Valida tipo, largo, rango y formato de todo lo que escribe el usuario. Los errores esperados se lanzan como `ValueError` con un mensaje claro para el usuario.

### 4.3 Crear acceso a datos

```python
"""Consultas de facturas."""

from datos.conexion import obtener_conexion


def pendientes_de(oid: str) -> list[dict]:
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "SELECT IdFactura, Numero, Monto FROM Factura WHERE Estado = ? AND IdResponsable = ?",
            ("Pendiente", oid),
        )
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
```

- Solo parámetros (`?`). Nunca f-strings, `+`, `%` ni `.format()` para armar SQL.
- Los datos de un usuario se filtran por `oid` **en la consulta**. Un registro ajeno se trata como inexistente.
- La cadena de conexión va en `secrets.toml` con un usuario de base de datos de permisos mínimos. Pide a IT el driver y los datos; no los inventes.

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
- Usa `usuario_actual()` o el valor de `requerir_permiso()`. Identifica al usuario por `usuario.oid`, nunca por correo o nombre.
- Llamadas a otras APIs o servicios externos: no las implementes por tu cuenta; pide al equipo dueño de la plantilla el mecanismo aprobado y regístralo como pendiente.
- **Prohibido** (lo verifica `tests/test_reglas_codigo.py`): `unsafe_allow_html=True`, `st.html`, componentes HTML/JS; SQL armado con texto; `eval`, `exec`, `pickle`, `shell=True`, `verify=False`; secretos en el código; `st.user`, `st.login`, `st.logout`, `st.navigation`, `st.set_page_config` fuera de la plantilla.
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

## 7. Convenciones SQL Server / Azure SQL

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

**Tamaño:** "Resumen vigente" en unas 10 líneas. Si el historial crece, mueve lo antiguo a `docs/historial/`.

## 10. Antes de dar por terminada una tarea

1. `.\.venv\Scripts\python.exe -m pytest` pasa completo (integridad, reglas de código y pruebas del módulo).
2. Cada página nueva: está en `PAGINAS`, empieza con `requerir_permiso`, usa `encabezado`, y su permiso existe en `config/permisos.toml`.
3. Cada servicio exige el permiso y valida entradas; los datos se filtran por `oid` cuando corresponde.
4. Se probó que un usuario sin el permiso no ve la página ni puede ejecutar la acción.
5. No hay secretos, tokens ni datos personales en código, registros ni `CONTEXTO_PROYECTO.md`.
6. `CONTEXTO_PROYECTO.md` actualizado con lo hecho, lo probado y la próxima acción.
7. Dile al usuario, en lenguaje simple, qué cambió y qué debe probar en el navegador.

## 11. Comandos (PowerShell, desde la carpeta del proyecto)

```powershell
powershell -ExecutionPolicy Bypass -File .\herramientas\preparar_proyecto.ps1   # preparar o reparar el entorno
.\.venv\Scripts\python.exe -m pytest                                              # pruebas
.\.venv\Scripts\python.exe herramientas\verificar_plantilla.py                    # integridad
.\.venv\Scripts\streamlit.exe run app.py                                          # abre http://localhost:8501
```
