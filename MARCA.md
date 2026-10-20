# MARCA.md — Estándar visual de las aplicaciones DELSUR

Fuente: *Sistema de diseño visual empresarial DELSUR* (basado en el Manual de Marca DELSUR 2019), traducido a Streamlit.

Codex: lee este archivo antes de crear o cambiar cualquier pantalla. **El diseño ya está construido**: el tema (`.streamlit/config.toml`) da colores y tipografía a todos los controles, y `interfaz/` trae el marco (barra lateral, barra superior con ruta, pie de página) y los componentes de marca. Tu trabajo es **usarlos**, no recrearlos. Las pruebas (`tests/test_reglas_codigo.py`) rechazan lo que se salga de esto.

## 1. Reglas que no se negocian

1. Cada página empieza con `requerir_permiso(...)` y luego **una** llamada a `encabezado(...)`.
2. Secciones con `seccion("Título")`. Nunca `st.title` ni `st.header` en las páginas.
3. Nada de colores escritos a mano (`#0058A2`, `:blue[...]`), CSS, HTML ni `st.set_page_config`. Si hace falta un color en un gráfico, usa `COLORES` de `interfaz.componentes`.
4. Íconos solo de Material: `icon=":material/nombre:"`. Sin emoji.
5. Números, montos, porcentajes y fechas siempre con `interfaz.formatos`.
6. Si algo no se puede lograr con los componentes, **no improvises**: anótalo como pendiente para el equipo dueño de la plantilla en `CONTEXTO_PROYECTO.md`.

## 2. Qué usar para cada cosa

| Necesidad | Usa | Ejemplo |
|---|---|---|
| Nombre, módulo, descripción y versión | `APLICACION = Aplicacion(...)` en `app.py` | se muestran en la pantalla de acceso, la barra superior y el pie |
| Menú lateral agrupado | `Pagina(..., grupo="Catálogos")` en `PAGINAS` | el menú agrupa por `grupo` en el orden de la lista |
| Panel de encabezado | `encabezado(titulo, descripcion, antetitulo, icono, estados)` | `encabezado("Cortes", "Consulta por zona.", antetitulo="Operaciones", icono="bolt")` |
| Estados bajo el encabezado | `Estado(texto, tipo)` | tipo `"exito"`, `"aviso"`, `"error"` o `"info"`; máximo 4 |
| Título de sección | `seccion(titulo)` | `seccion("Resultados")` (se muestra en mayúsculas) |
| Agrupar contenido | `with tarjeta(titulo, acento):` | acento `"azul"` (general), `"cyan"` (interacción, información), `"lima"` (energía, logros; con moderación) |
| Indicadores clave (KPI) | `fila_indicadores([Indicador(etiqueta, valor, detalle, icono)], columnas=2)` | hasta 4 por fila; `icono` es un nombre Material (`"payments"`) |
| Acción principal | `st.button(..., type="primary")` | **una** por sección |
| Acción secundaria | `st.button(...)` | |
| Eliminar o anular | `confirmar_accion(clave, mensaje, etiqueta)` | pide confirmación |
| Formularios | `st.form` dentro de una `tarjeta` | cada campo con etiqueta visible |
| Mensajes | `st.success` / `st.info` / `st.warning` / `st.error` | ya tienen los colores semánticos |
| Tablas | `st.dataframe(..., hide_index=True)` | columnas con nombres legibles |
| Gráficos | `st.bar_chart`, `st.line_chart`, Altair | usan la paleta de marca automáticamente |
| Pestañas | `st.tabs` | |
| Navegación entre páginas | `st.page_link` | |

Ejemplo de página completa:

```python
import streamlit as st

from interfaz import Estado, Indicador, encabezado, fila_indicadores, formatos, seccion, tarjeta
from seguridad import requerir_permiso

usuario = requerir_permiso("cortes:ver")

encabezado(
    "Cortes programados",
    "Consulte los cortes por zona y fecha.",
    antetitulo="Operaciones / Cortes",
    icono="bolt",
    estados=[Estado("Datos: actualizado")],
)
fila_indicadores([
    Indicador("Cortes esta semana", formatos.numero(12), "3 en Santa Tecla", icono="bolt"),
    Indicador("Clientes afectados", formatos.numero(3480), "Zona occidental", icono="groups", acento="cyan"),
])

seccion("Filtros")
with tarjeta(acento="cyan"):
    zona = st.selectbox("Zona", ["Santa Tecla", "La Libertad"])

seccion("Resultados")
st.dataframe(datos, hide_index=True)
```

## 3. Estructura de cada pantalla

El marco lo pone `ejecutar_aplicacion` en `app.py` y no se toca: pantalla de acceso dividida (marca a la izquierda, usuario y contraseña a la derecha, sin menú); barra lateral azul con logo, menú agrupado y usuario con rol al fondo; barra superior con la ruta navegable (aplicación / grupo / página), el ambiente y el estado de conexión; pie con nombre, descripción, versión, ambiente y área responsable.

Dentro de cada página:

1. `encabezado` (antetítulo = módulo o área; descripción = una o dos líneas que digan para qué sirve).
2. Indicadores, si la página los necesita.
3. Filtros en una tarjeta cyan; resultados debajo.
4. Máximo una acción primaria por sección; las destructivas con `confirmar_accion`.
5. El logo, el menú, la ruta, la tarjeta de usuario y el pie ya los pone la plantilla.

## 4. Colores (referencia; ya están en el tema)

| Token | Valor | Uso |
|---|---|---|
| Azul 286 | `#0058A2` | Color principal: títulos, botón primario, enlaces |
| Cyan | `#009FE3` | Interacción y foco; acento de tarjetas informativas |
| Lima EPM | `#9DC431` | Solo como línea fina o acento de "energía" |
| Verde EPM | `#007934` | Éxito |
| Gris Cool Gray 11 | `#706F6F` | Texto secundario |
| Tinta | `#2C2E35` | Texto principal |
| Azul profundo | `#0B2E57` | Barra lateral y pie de página |
| Azul claro | `#EEF3FA` / `#DCE6F4` | Panel de encabezado |
| Gris 50 | `#F6F6F6` | Fondo de la página (las tarjetas son blancas) |
| Error / Aviso | `#B42318` / `#B7791F` | Solo mensajes de estado |

Prohibido: degradados, sombras fuertes, rojo/naranja/magenta como color decorativo, recolorear el logo.

## 5. Tipografía

Montserrat 800 para títulos (sustituye a Aharoni del manual) y Source Sans 3 para texto (sustituye a Myriad Pro). Vienen incluidas en la plantilla; no se cargan de internet.

## 6. Logo

Lo coloca la plantilla en la barra lateral y en el pie (versión blanca oficial, 150 px y 140 px, con endoso Grupo EPM). Nunca agregues otro logo, no lo separes del endoso, no lo deformes ni lo recolorees, y no uses el sol como ícono.

## 7. Textos y tono

- Español de El Salvador, registro institucional; trato de **usted**.
- Siempre **DELSUR** (una palabra, mayúsculas). Endoso en texto: "Grupo EPM".
- Botones con verbo en infinitivo: "Guardar", "Buscar", "Exportar".
- Mensajes de error que digan qué pasó y qué hacer, sin detalles técnicos.
- Sin emoji ni signos de exclamación.

## 8. Formatos (`interfaz.formatos`)

| Dato | Función | Resultado |
|---|---|---|
| Moneda (USD) | `formatos.moneda(1234.5)` | `$1,234.50` |
| Número | `formatos.numero(1234)` | `1,234` |
| Porcentaje | `formatos.porcentaje(0.125)` | `12.5 %` |
| Fecha | `formatos.fecha(d)` | `15/10/2026` |
| Fecha y hora | `formatos.fecha_hora(dt)` | `15/10/2026 13:54` (hora de El Salvador) |

## 9. Accesibilidad

- Todo campo con etiqueta visible; no usar solo el texto de ayuda dentro del campo.
- No transmitir información solo con color: acompáñalo de texto o ícono.
- El cyan no se usa para texto sobre blanco (contraste insuficiente); el tema ya lo resuelve.
