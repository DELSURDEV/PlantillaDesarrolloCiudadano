# Guía de desarrollo ciudadano con la plantilla DELSUR

Guía práctica para crear una aplicación interna con ayuda de un asistente de inteligencia artificial (IA), a partir de la plantilla corporativa de DELSUR.

- **Para quién es:** personas que conocen bien su proceso de trabajo, pero que no programan ni administran servidores.
- **Para qué sirve esta etapa:** la plantilla está en una etapa temprana y está pensada para **desarrollar y probar aplicaciones internas en el RDP** (el escritorio remoto). La publicación para otros usuarios es una etapa futura.
- **Asistente de IA:** las instrucciones de la plantilla (`AGENTS.md`) están escritas para **Codex**. En esta guía, "el asistente" significa Codex.
- **Estado:** la plantilla está pendiente de revisión y aprobación de IT.

> **Sobre la versión.** Esta guía forma parte de la plantilla desde la versión 0.7.0. Los proyectos creados con la v0.6.2 no incluyen esta guía ni los scripts para abrir la aplicación en otro puerto y para ejecutar las pruebas, y su script de preparación borra la carpeta `.git` al volver a ejecutarse. Si su proyecto se creó con la v0.6.2, **no cree un repositorio Git dentro de él** hasta que el equipo dueño de la plantilla indique cómo actualizarlo. La versión de su proyecto está en el archivo `VERSION`.

Los textos marcados como **[PENDIENTE: …]** son datos que esta guía no puede confirmar y que deben definir IT o el equipo dueño de la plantilla.

---

## Primeros pasos (recorrido corto)

1. **Confirme con IT sus accesos** (sección B): el RDP, Codex, Python, el disco `E:` y su cuenta de desarrollo en WAPI_ACCESS con rol `ADMINISTRADOR` o `USUARIO`.
2. **Prepare su idea** en una hoja: qué problema resuelve, quién la usa, qué datos maneja y qué reglas aplican (sección E).
3. **Obtenga la plantilla:** abra Codex en `E:\` y escriba *"Quiero crear una aplicación nueva."* Codex le propone su usuario para que lo confirme, pide el nombre del proyecto, descarga la versión aprobada en `E:\<usuario>\<nombre>` y la prepara (sección C).
4. **Compruebe que quedó lista:** al final debe aparecer en verde *"Proyecto '<nombre>' listo (plantilla v…, sin relación con su repositorio)."*
5. **Abra Codex dentro de la carpeta del proyecto** (`E:\<usuario>\<nombre>`) y escriba *"Lee AGENTS.md y CONTEXTO_PROYECTO.md y ayúdame a definir el proyecto."*
6. **Vea la aplicación:** escriba *"Abre la aplicación."* Se abre una ventana negra y el navegador en `http://localhost:8501`. Entre con su usuario y contraseña corporativos.
7. **Construya por partes pequeñas** (sección F): describa una funcionalidad, revise la propuesta, deje que Codex la construya y pruébela.
8. **Antes de irse** escriba *"Guarda el avance, voy a cerrar."* **Para retomar** otro día, escriba *"Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa."* (sección H).

---

## A. Qué permite hacer la plantilla

### Para qué sirve

La plantilla es una **base ya construida** para aplicaciones web internas sencillas: formularios, validaciones, revisiones de archivos, consultas y reportes. Usted describe lo que necesita y Codex lo construye dentro de esa base, sin tener que resolver el inicio de sesión, la seguridad ni el diseño.

La aplicación está hecha con **Streamlit** (una herramienta de Python para crear páginas web de datos). No necesita conocerla: Codex la usa por usted.

### Qué trae ya preparado

| Elemento | Qué significa para usted |
|---|---|
| Inicio de sesión interno | La aplicación pide su usuario y contraseña corporativos y los valida con **WAPI_ACCESS**, el servicio interno de accesos, usando el código de aplicación `/DCIU`. Ya viene configurado. |
| Roles y permisos | WAPI_ACCESS indica el rol del usuario (`ADMINISTRADOR` o `USUARIO`). Su proyecto decide qué pantallas y acciones corresponden a cada rol. |
| Sesión segura | La sesión dura como máximo 8 horas y se cierra tras 30 minutos sin actividad. Recargar la página o abrir otra pestaña pide iniciar sesión de nuevo. Tras 5 intentos fallidos el usuario queda bloqueado 15 minutos. |
| Registro de seguridad | Se anotan inicios de sesión, bloqueos y accesos denegados, nunca contraseñas. Se muestra en la ventana negra de la aplicación. |
| Diseño DELSUR | Menú lateral, barra superior con la ruta, pie de página, colores, tipografía y logo oficiales. |
| Reglas automáticas | Pruebas que rechazan código inseguro o que se salga del diseño. |
| Memoria del proyecto | El archivo `CONTEXTO_PROYECTO.md` guarda el avance entre sesiones. |
| Página de ejemplo | Solo trae la página "Inicio" con un saludo. Todo lo demás lo construye usted con Codex. |

### Cómo funciona el inicio de sesión

Es una autenticación interna con usuario y contraseña. Se eligió para que usted **no tenga que configurar ni guardar credenciales de la aplicación**.

1. Usted escribe su usuario y contraseña en la pantalla de acceso de la aplicación.
2. La aplicación los envía a WAPI_ACCESS desde el RDP, junto con el código `/DCIU`. El navegador nunca se comunica directamente con WAPI_ACCESS.
3. WAPI_ACCESS responde quién es usted y sus roles. La aplicación conserva solo su usuario, su nombre y sus roles. La contraseña no se guarda y cualquier otro dato de la respuesta (por ejemplo, un token) se descarta.

Detalles que conviene saber:

- La aplicación solo se comunica con WAPI_ACCESS. Si WAPI_ACCESS consulta a su vez al proveedor de identidad interno (IdentityServer), eso ocurre dentro de la infraestructura de IT y no forma parte de la aplicación.
- **No es un inicio de sesión único (SSO):** cada aplicación le pide usuario y contraseña, y la sesión no se comparte con otras aplicaciones ni con otras pestañas.
- WAPI_ACCESS solo se alcanza desde la red corporativa, es decir, desde el RDP.

### Identidad, permisos y acceso a datos son cosas distintas

| Concepto | Qué responde | Quién lo resuelve hoy |
|---|---|---|
| **Identidad** | ¿Quién es esta persona? | WAPI_ACCESS (usuario, nombre y roles). |
| **Autorización** | ¿Qué puede hacer en esta aplicación? | Su proyecto, con los permisos de cada rol, verificados por la aplicación en el servidor. |
| **Acceso a datos** | ¿Puede la aplicación leer o guardar información en un sistema interno? | **Nadie todavía.** Saber quién es el usuario no le da a la aplicación permiso para usar bases de datos u otros sistemas. Para eso se necesitan servicios y acuerdos adicionales, que son una etapa futura. |

### Qué puede y qué no puede guardar la aplicación

Según el código actual:

- Lo que el usuario escribe o carga vive solo en **la sesión de su pestaña**. Se pierde al recargar la página, cerrar la pestaña, vencer la sesión o cerrar la ventana negra de la aplicación.
- Se pueden cargar archivos de hasta 10 MB para revisarlos o procesarlos durante la sesión.
- La aplicación puede generar un archivo con los resultados para que el usuario lo descargue (por ejemplo, un CSV).
- La plantilla **no incluye** ningún mecanismo para guardar información de forma permanente ni para compartirla entre usuarios, y no se conecta a bases de datos ni a otros sistemas internos. Esa capacidad no está definida todavía; es una decisión de alcance para una etapa futura.

Por eso, hoy encajan mejor los procesos que **se resuelven dentro de una sesión**: revisar un archivo y obtener un reporte, validar datos antes de enviarlos por otro medio, calcular o simular. Si su proceso necesita guardar registros (por ejemplo, solicitudes que otra persona aprueba días después), Codex puede construir y probar las pantallas y reglas, pero los datos no se conservarán; esa necesidad queda registrada como pendiente.

### Qué debe describir usted

- El problema que quiere resolver y el resultado esperado.
- Quién usa la aplicación y qué puede hacer cada tipo de usuario.
- Qué datos se capturan, cargan o reportan.
- Las reglas del proceso (montos máximos, fechas límite, campos obligatorios, validaciones).
- Cómo sabrá que la aplicación funciona (criterios de aceptación).

No necesita decidir tecnología, estructura de archivos, seguridad ni diseño: la plantilla ya lo resuelve.

### Condiciones conocidas de esta etapa

| Tema | Situación |
|---|---|
| **Uso** | Desarrollo y pruebas internas en el RDP. No es una publicación para otros usuarios. |
| **Comunicación con WAPI_ACCESS** | Hoy usa HTTP: entre la aplicación y WAPI_ACCESS, la contraseña viaja **sin cifrar** por la red interna. Es una condición conocida por el responsable del proyecto, aceptada solo para desarrollo y pruebas internas. No es una conexión cifrada ni una aprobación para producción; para producción, la plantilla exige HTTPS o una excepción registrada por IT. Entre su navegador y la aplicación, la comunicación queda dentro del mismo RDP (`localhost`). |
| **Cuentas** | Cada persona usa su propia cuenta de desarrollo, creada por IT. No hay cuentas compartidas ni usuarios de prueba simulados. |
| **Datos y otros sistemas** | Fuera del alcance actual (ver arriba). |
| **Publicación** | Etapa futura, sin procedimiento definido. |
| **Íconos** | Se descargan de `fonts.gstatic.com`. Si ese sitio está bloqueado, los íconos aparecen como texto. |

---

## B. Antes de comenzar

### Accesos y herramientas (los entrega IT)

| Necesita | Para qué | Cómo comprobarlo |
|---|---|---|
| RDP con Windows y red corporativa | Trabajar y llegar a WAPI_ACCESS | Puede abrir el escritorio remoto. |
| Disco `E:` en el RDP (su etiqueta es "Data") | Guardar sus proyectos | En el Explorador de archivos aparece como *Data (E:)*. |
| Codex instalado y con acceso | El asistente que construye la aplicación | **[PENDIENTE IT: cómo se abre Codex en el RDP]** |
| Python 3.10 o superior | Ejecutar la aplicación | El script de preparación lo busca solo. Si falta, muestra *"No se encontró Python 3.10 o superior. Pida a IT que lo instale."* |
| Acceso a `github.com` y `raw.githubusercontent.com` | Descargar la plantilla | La descarga termina sin error. |
| Acceso a PyPI (el repositorio público de librerías de Python), directo o por proxy | Instalar las librerías (unos 90 MB la primera vez) | El script no muestra *"No se pudieron instalar las librerías…"*. |
| PowerShell con permiso para `-ExecutionPolicy Bypass` | Ejecutar los scripts de la plantilla | Los scripts corren sin el error de "ejecución de scripts deshabilitada". |
| Su cuenta de desarrollo en WAPI_ACCESS, aplicación `/DCIU`, con rol `ADMINISTRADOR` o `USUARIO` | Entrar a su aplicación | Puede iniciar sesión en `http://localhost:8501`. |

No se necesitan permisos de administrador ni Git.

### Dónde guardar su trabajo

**Guarde cada proyecto en `E:\<usuario>\<proyecto>`**: una carpeta con su usuario y, dentro, una carpeta por proyecto. Por ejemplo, `E:\kehernandez\GTMP` y `E:\kehernandez\revision-lecturas`. `Data` es el nombre del disco, no una carpeta. No use el escritorio, "Documentos", "Descargas" ni otras carpetas de `C:`.

La primera vez, Codex crea su carpeta de usuario. Los siguientes proyectos se crean dentro de esa misma carpeta, sin tocar los que ya tiene. Antes de crear nada, Codex le propone su usuario de Windows para que lo confirme. Es solo el nombre de la carpeta: nunca le pedirá su contraseña.

Lo que todavía **no está comprobado** es que el disco conserve los archivos después de cada limpieza o reinicio del RDP, que un usuario normal pueda crear su carpeta en `E:\`, quién más puede ver su contenido y si tiene respaldo. Tener una carpeta propia no impide por sí solo que otros usuarios la vean. **[PENDIENTE IT: confirmar persistencia, permisos y respaldo del disco `E:`]**

Para comprobar usted mismo que su carpeta se conserva:

1. Después de crear el proyecto, abra el Explorador de archivos y entre a `E:\<usuario>\<nombre>`.
2. Confirme que ve, entre otros, `AGENTS.md`, `CONTEXTO_PROYECTO.md`, `app.py` y la carpeta `.venv`.
3. Cierre la sesión del RDP. Después de un reinicio o al día siguiente, vuelva a entrar a la misma carpeta.
4. Resultado esperado: los archivos siguen ahí y `CONTEXTO_PROYECTO.md` tiene la fecha de su última actualización.
   - Si **solo falta** la carpeta `.venv`, el proyecto está bien: Codex la vuelve a crear al iniciar (sección H).
   - Si **falta toda la carpeta** o `CONTEXTO_PROYECTO.md` volvió a un estado anterior, avise a IT y deje de trabajar en esa ubicación hasta que lo resuelvan.

### Información funcional que conviene preparar

- Nombre corto del proyecto: letras, números, `-` o `_`, de 3 a 50 caracteres, sin espacios ni tildes. Ejemplo: `revision-lecturas`.
- Descripción del problema en 3 a 5 líneas.
- Qué hace en la aplicación un `USUARIO` y qué hace un `ADMINISTRADOR`.
- Campos de cada formulario, o columnas de los archivos que se cargan.
- Reglas del proceso, con ejemplos de casos que deben aceptarse y rechazarse.
- Ejemplos de reportes o pantallas actuales (Excel, capturas, dibujos). Use datos ficticios.
- Si los datos son sensibles (personales, financieros), dígalo desde el inicio.

### Lo que entrega o resuelve IT

| Tema | Detalle |
|---|---|
| Cuenta de desarrollo | Una cuenta por persona en WAPI_ACCESS, con rol `ADMINISTRADOR` o `USUARIO` en `/DCIU`. |
| Cuentas para probar permisos | Para comprobar en pantalla que alguien con otro rol no ve lo que no debe, hace falta otra cuenta real con ese rol. |
| Roles nuevos | Si su proyecto necesita un rol distinto de `ADMINISTRADOR` y `USUARIO`, IT debe crearlo en WAPI_ACCESS. |
| Disco `E:` | Confirmar que se conserva, que cada usuario puede crear su carpeta, quién tiene acceso y su respaldo. |
| Herramientas | Python, Codex, acceso a GitHub y PyPI, y permiso para los scripts de PowerShell. |

---

## C. Cómo obtener y preparar la plantilla

La plantilla se descarga como un archivo comprimido (ZIP) de una **versión aprobada** (por ejemplo `v0.7.1`) desde GitHub. Solo se copian los archivos: **no se trae el historial ni la conexión con el repositorio de la plantilla**. Así, nada de lo que usted haga puede enviarse por accidente a la plantilla. No necesita Git.

### Paso previo: archivo de arranque en `E:\`

Codex necesita un archivo de instrucciones de arranque (`AGENTS.md`) en la raíz del disco, `E:\`. Si IT no lo dejó colocado:

1. Abra PowerShell (menú Inicio → escriba *PowerShell*).
2. Escriba y ejecute:
   ```powershell
   cd "E:\"
   Invoke-WebRequest "https://raw.githubusercontent.com/DELSURDEV/PlantillaDesarrolloCiudadano/v0.7.1/herramientas/AGENTS_ARRANQUE.md" -OutFile ".\AGENTS.md" -UseBasicParsing
   ```
3. Resultado esperado: aparece `AGENTS.md` en `E:\`. Si Windows no le permite guardarlo ahí, pida a IT que lo coloque.

### Camino 1: Codex crea el proyecto (recomendado)

1. Abra Codex **en `E:\`**.
2. Escriba: *"Quiero crear una aplicación nueva."*
3. Codex le propone su usuario de Windows: *"¿Tu usuario es kehernandez?"*. Confírmelo o escriba el correcto.
4. Codex le pide el nombre del proyecto. Respóndalo (ejemplo: `GTMP`).
5. Codex crea su carpeta de usuario si no existe, descarga la versión aprobada en `E:\<usuario>\<nombre>` y ejecuta la preparación. La primera vez tarda unos minutos.
6. Si un paso falla, Codex debe mostrarle el mensaje y detenerse. No debe armar el proyecto a mano ni descargarlo por otro medio.

### Camino 2: descarga manual (si Codex no puede ejecutarla)

1. Abra el archivo `E:\AGENTS.md` con el Bloc de notas.
2. Busque la sección **"Crear un proyecto nuevo"**, paso 3, y copie el bloque de comandos completo.
3. Péguelo en PowerShell, cambie `<USUARIO>` por su usuario y `<NOMBRE>` por el nombre del proyecto, y presione Enter.

Es el mismo procedimiento que usa Codex: reutiliza su carpeta de usuario, se detiene si el proyecto ya existe, no sobrescribe nada y no deja archivos temporales.

### Qué hace la preparación

El script `herramientas\preparar_proyecto.ps1` (no requiere permisos de administrador):

1. Comprueba que la carpeta no sea una copia conectada al repositorio de la plantilla. Si lo es, se detiene sin cambiar nada.
2. La primera vez, anota en `CONTEXTO_PROYECTO.md` el nombre, la ruta, la versión de la plantilla y la fecha. Si el archivo ya tiene su avance, no lo toca.
3. Crea `.streamlit\secrets.toml` a partir del ejemplo, solo si no existe (no contiene contraseñas).
4. Crea el entorno de Python del proyecto (carpeta `.venv`) e instala las librerías con versiones fijas.
5. Verifica que la base de seguridad no fue modificada y corre las pruebas automáticas.

Se puede volver a ejecutar sin riesgo: solo reconstruye lo necesario para ejecutar el proyecto. **Nunca borra ni modifica un repositorio Git** que usted haya creado, tampoco los que estén dentro de subcarpetas.

### Cómo comprobar que terminó bien

Debe ver líneas que empiezan con `==>` y, al final:

- `Plantilla íntegra.`
- Un resumen de pruebas con la palabra `passed` y sin `failed`.
- En verde: `Proyecto '<nombre>' listo (plantilla v…, sin relación con su repositorio).`

Si aparece la advertencia *"El proyecto no está en E:\<usuario>\<proyecto>"*, el proyecto quedó en otra ubicación: pida ayuda antes de seguir trabajando en él. Si aparece un mensaje en rojo, vea la sección I.

### Dónde queda registrada la versión

- Archivo `VERSION` del proyecto.
- `CONTEXTO_PROYECTO.md`, fila **Plantilla de origen**.

Anote esa versión en cualquier consulta a IT. Las copias existentes **no se actualizan solas** cuando sale una versión nueva de la plantilla.

### Si más adelante quiere usar Git (opcional)

Al inicio no se usa Git. Si más adelante quiere llevar un historial de cambios, pida a Codex crear un **repositorio nuevo y propio** dentro de la carpeta del proyecto. Nunca lo conecte al repositorio de la plantilla. A partir de la v0.7.0, volver a preparar el entorno conserva su repositorio completo: historial, rama y configuración. En proyectos creados con la v0.6.2, vea el aviso al inicio de esta guía.

---

## D. Primera configuración y autenticación

### Qué se genera automáticamente

| Archivo | Lo crea | Contenido |
|---|---|---|
| `.streamlit\secrets.toml` | El script de preparación, copiando `secrets.toml.example` | Ambiente (`desarrollo`), duración de sesión, intentos permitidos y tiempo de espera de WAPI_ACCESS. **No contiene contraseñas.** |
| `CONTEXTO_PROYECTO.md` (datos iniciales) | El script de preparación | Nombre, ruta, versión de plantilla y fecha. |
| `.venv\` | El script de preparación | Las librerías del proyecto. |

### Qué aporta cada quien

| Quién | Qué aporta |
|---|---|
| **IT** | Su cuenta de desarrollo en WAPI_ACCESS con el rol correspondiente en `/DCIU`. La dirección de WAPI_ACCESS y el código `/DCIU` ya vienen fijos en la plantilla. |
| **Usted** | Su usuario y contraseña, **solo en la pantalla de acceso de la aplicación**. Además, define con Codex el nombre de la aplicación y qué puede hacer cada rol. |
| **Codex** | Cambia el nombre y la descripción de la aplicación en `app.py` y asigna permisos a cada rol en `config/permisos.toml`. |

No hay que configurar tenant, identificadores de aplicación, secretos ni direcciones de retorno: el inicio de sesión interno no los usa.

### Cómo funcionan los roles

1. Usted inicia sesión y WAPI_ACCESS informa su rol: `ADMINISTRADOR` o `USUARIO`.
2. El archivo `config/permisos.toml` dice qué **permisos** tiene cada rol (ejemplo: `revision:cargar`, `revision:ver_resumen`).
3. La aplicación muestra solo las pantallas y acciones que esos permisos permiten, y vuelve a comprobarlo en el servidor cada vez que alguien ejecuta una acción. Ocultar un botón no es la única protección.

Un rol que no esté en `config/permisos.toml` no recibe ningún permiso.

### Información privada

- **Nunca** escriba contraseñas ni tokens en el chat, en el código ni en `CONTEXTO_PROYECTO.md`.
- La plantilla no necesita ningún secreto para funcionar en esta etapa.
- Nunca pida a Codex desactivar el inicio de sesión, crear usuarios de prueba, usar cuentas compartidas ni "simular" el acceso para avanzar. La plantilla lo prohíbe y las pruebas lo detectan.

### Cómo reconocer una configuración incompleta

La aplicación **no abre** si la configuración no es segura. En lugar del inicio de sesión verá uno de estos mensajes:

| Mensaje | Qué significa |
|---|---|
| *"La aplicación está cerrada porque su configuración de seguridad está incompleta."* (con una lista debajo) | Un valor de `secrets.toml` o `config/permisos.toml` es inválido. Copie la lista a Codex. |
| *"La aplicación está cerrada por un error en PAGINAS de app.py: …"* | Una pantalla exige un permiso que no existe en `config/permisos.toml`, o está repetida. Pida a Codex que lo corrija. |
| *"Su usuario no tiene un rol con acceso a esta aplicación. Solicite el acceso a IT."* | Entró bien, pero su rol no tiene permisos en este proyecto. |

---

## E. Cómo solicitar una nueva solución

### Ejemplo de mensaje inicial

Copie, adapte y envíe a Codex en la carpeta del proyecto:

```text
Lee AGENTS.md, MARCA.md y CONTEXTO_PROYECTO.md. Quiero definir el proyecto antes de construir.
Reutiliza la base de la plantilla y sus puntos de extensión; no modifiques la zona protegida.

Problema: Cada mes revisamos a mano un archivo CSV con lecturas de medidores exportado del
sistema comercial. Buscamos lecturas negativas, consumos fuera de lo normal y campos vacíos.
La revisión toma dos días y se escapan errores.

Usuarios y responsabilidades:
- USUARIO (analista): carga el archivo, revisa las inconsistencias y descarga el reporte.
- ADMINISTRADOR (jefe de área): además ve un resumen por zona.

Datos:
- Archivo CSV de hasta 10 MB con columnas: zona, número de medidor, lectura anterior,
  lectura actual, fecha de lectura.

Pantallas o reportes:
1. Cargar archivo y validar columnas.
2. Lista de inconsistencias con filtro por tipo y zona.
3. Resumen por zona (solo ADMINISTRADOR).
4. Descarga del reporte de inconsistencias en CSV.

Reglas:
- Lectura actual menor que la anterior: "lectura negativa".
- Consumo mayor a 3 veces el promedio de la zona: "consumo atípico".
- Fecha de lectura fuera del mes revisado: "fecha fuera de periodo".
- Si faltan columnas, el archivo se rechaza con un mensaje claro.

Resultado esperado: hacer la revisión en menos de una hora, con el mismo criterio para todos.

Antes de construir: resume lo que entendiste, propón los permisos de cada rol, indica qué
queda fuera del alcance de esta versión de la plantilla y registra el alcance y los criterios
de aceptación en CONTEXTO_PROYECTO.md. No construyas todavía.
```

### Cómo revisar el alcance antes de construir

Codex debe responderle con un resumen. Revise que:

1. **Repita el problema con sus palabras** y no agregue funciones que usted no pidió.
2. **Proponga permisos claros para cada rol**, por ejemplo: `USUARIO` con `revision:cargar`, y `ADMINISTRADOR` con `revision:cargar` y `revision:ver_resumen`.
3. **Advierta lo que no se puede hacer en esta etapa**: guardar información de forma permanente, conectarse a bases de datos u otros sistemas.
4. **Liste lo que necesita de IT**, por ejemplo un rol nuevo.
5. **Diga qué queda fuera del alcance.**
6. **Proponga criterios de aceptación verificables**, por ejemplo: *"Un USUARIO no ve el resumen por zona."*
7. **Proponga un orden de construcción** en partes pequeñas.

Para comprobar que entendió, hágale preguntas sobre casos concretos:

- *"¿Qué pasa si el archivo no tiene la columna de zona?"*
- *"¿Qué ve un USUARIO si escribe la dirección de la pantalla de resumen?"*
- *"¿Qué pasa si una zona tiene un solo medidor?"*

Si las respuestas coinciden con su proceso, pida: *"Registra el alcance y los criterios en CONTEXTO_PROYECTO.md."* Abra ese archivo y confírmelo.

---

## F. Cómo desarrollar una funcionalidad

### El ciclo de trabajo

| Paso | Qué hace usted | Qué hace Codex | Resultado que debe ver |
|---|---|---|---|
| 1. Explicar la necesidad | Describe una sola funcionalidad. | Pregunta lo que falte. | Una pregunta o un resumen. |
| 2. Aclarar reglas y permisos | Responde quién puede usarla y qué reglas aplican. | Propone el permiso (`modulo:accion`) y a qué rol se asigna. | Una lista de permisos y roles. |
| 3. Revisar la propuesta | Lee el plan y lo aprueba o corrige. | Explica en pocas líneas qué archivos creará. | Un plan corto. |
| 4. Construir una parte pequeña | Aprueba un paso a la vez. | Crea la pantalla, sus reglas y sus pruebas. | Archivos nuevos en `paginas/`, `servicios/` y `tests/`. |
| 5. Ejecutar las verificaciones | Pide que corra las pruebas. | Ejecuta las pruebas y la verificación de integridad. | Todas las pruebas pasan. |
| 6. Probar el comportamiento | Prueba en el navegador (sección G). | Le dice qué probar. | La pantalla se comporta como espera. |
| 7. Registrar | Confirma. | Actualiza `CONTEXTO_PROYECTO.md`. | La línea *"Contexto actualizado: …"* al final de la respuesta. |

Construya por partes: primero la carga del archivo, luego la lista, luego el resumen. Es más fácil probar y corregir.

### Cómo usar mockups y ejemplos

Un **mockup** es un dibujo o captura de cómo quiere que se vea una pantalla. Puede compartir:

- Una captura o dibujo de la pantalla deseada.
- Un Excel o CSV de ejemplo con las columnas del reporte.
- Un formulario en papel o PDF que hoy se usa.

Codex los usa como **referencia de contenido** (qué campos, qué columnas, en qué orden), pero construye con los componentes y colores de DELSUR que trae la plantilla. No copiará colores, HTML ni estilos del ejemplo, y no quitará el inicio de sesión ni los permisos.

Use datos ficticios o sin información personal en los ejemplos.

### Mensajes listos para copiar

**Crear una funcionalidad**

```text
Quiero agregar la pantalla "Cargar archivo" del proyecto.
Reutiliza la base de la plantilla y sus puntos de extensión (PAGINAS en app.py,
config/permisos.toml, paginas/, servicios/, componentes de interfaz/). No modifiques la zona protegida.

Quién la usa: los roles USUARIO y ADMINISTRADOR.
Qué hace: cargar un CSV de hasta 10 MB y comprobar que tenga las columnas zona, medidor,
lectura anterior, lectura actual y fecha.
Reglas: si falta una columna, rechazar el archivo y decir cuál falta.
Al terminar la carga: mostrar cuántas filas se leyeron.

Primero explica tu plan en pocas líneas y espera mi aprobación. Al terminar, corre las
pruebas, dime qué debo probar en el navegador y actualiza CONTEXTO_PROYECTO.md.
```

**Modificar una pantalla o una regla**

```text
Quiero cambiar la pantalla "Inconsistencias".
Cambio: agregar un filtro por zona y ordenar por consumo, de mayor a menor.
Regla nueva: el consumo atípico es mayor a 2.5 veces el promedio de la zona (antes era 3).
Mantén la base de la plantilla, sus componentes y el control de permisos.
Explica el plan antes de cambiar, corre las pruebas al final y actualiza CONTEXTO_PROYECTO.md.
```

**Reportar un error**

```text
Encontré un error en la pantalla "Resumen por zona".
Pasos:
1. Inicié sesión con mi cuenta de rol ADMINISTRADOR.
2. Cargué el archivo de ejemplo de junio.
3. Abrí "Resumen por zona".
Resultado esperado: una fila por zona con su total de inconsistencias.
Resultado observado: la zona "Occidente" aparece dos veces.
Mensaje que apareció (copiado tal cual): <pegue aquí el texto, sin contraseñas>
Revisa la causa, corrígela sin quitar controles de seguridad, agrega una prueba para este caso,
corre las pruebas y registra el error y la corrección en CONTEXTO_PROYECTO.md.
```

### Lo que Codex no debe hacer (aunque se lo pida)

- Modificar la zona protegida: `seguridad/`, `interfaz/`, `static/`, `recursos/`, `herramientas/`, `.streamlit/config.toml`, `restricciones.txt` y las pruebas de la plantilla.
- Desactivar el inicio de sesión, crear usuarios de prueba, usar cuentas compartidas o simular WAPI_ACCESS.
- Conectarse a bases de datos, otros sistemas o APIs.
- Inventar servidores, bases de datos o roles.
- Borrar, mover o reiniciar carpetas de proyectos o repositorios Git.

Si su necesidad exige algo de esta lista, Codex debe explicarlo y registrarlo como pendiente para el equipo dueño de la plantilla.

---

## G. Cómo ejecutar y probar

Todo se hace **desde la carpeta del proyecto** (`E:\<usuario>\<nombre>`). Lo más sencillo es pedírselo a Codex con las frases indicadas.

### Abrir la aplicación

1. Escriba a Codex: *"Abre la aplicación."*
2. Codex ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\herramientas\abrir_aplicacion.ps1
   ```
3. Resultado esperado: se abre una **ventana negra** (la aplicación funcionando), aparece el mensaje *"Aplicación abierta en http://localhost:8501"* y el navegador se abre en esa dirección con la pantalla de acceso de DELSUR.
4. Entre con su usuario y contraseña corporativos.
5. Resultado esperado: ve el menú lateral con las pantallas que su rol permite, la barra superior con la etiqueta **Desarrollo** y la página **Inicio**.

### Si el puerto 8501 está ocupado

El **puerto** es el número al final de la dirección (`:8501`). Si ya hay una aplicación usando ese número, el script no abre otra ni cierra ningún programa. Muestra un mensaje como este:

> El puerto 8501 ya está en uso: hay otra aplicación abierta (o esta misma).

Qué hacer:

1. Si es **esta misma aplicación**, abra `http://localhost:8501` en el navegador y recargue la página.
2. Si es **otra aplicación** que ya no necesita, ciérrela desde su ventana negra y vuelva a pedir *"Abre la aplicación."*
3. Si quiere tener las dos abiertas, pida a Codex *"Abre la aplicación en el puerto 8502."* El script la abre en `http://localhost:8502` y el navegador va a esa dirección. Use siempre la dirección que muestra el mensaje.

No es necesario ni permitido cambiar archivos de configuración para usar otro puerto.

### Ver un cambio

Los cambios se aplican solos en unos segundos. Si no aparecen, recargue con **F5** y vuelva a iniciar sesión (recargar siempre cierra la sesión; es normal).

### Detener la aplicación

Cierre la ventana negra. El navegador dejará de responder; eso es lo esperado.

### Los cuatro tipos de prueba

| Tipo | Quién | Cómo | Resultado esperado |
|---|---|---|---|
| **Pruebas automatizadas** | Codex | Escriba *"Corre las pruebas."* Codex ejecuta `powershell -ExecutionPolicy Bypass -File .\herramientas\ejecutar_pruebas.ps1` y `.\.venv\Scripts\python.exe herramientas\verificar_plantilla.py`. | `passed` sin `failed`, y `Plantilla íntegra.` Si alguna prueba aparece como omitida ("no disponible"), pida a Codex que explique por qué. Revisan seguridad, reglas de código, diseño, los scripts de la plantilla y las reglas de su proceso. |
| **Revisión visual** | Usted | Abra cada pantalla nueva. | Usa el diseño DELSUR, los textos se entienden, los botones dicen lo que hacen, montos y fechas tienen el formato correcto. |
| **Prueba del proceso** | Usted y usuarios clave, cada uno con su cuenta | Recorra los casos de los criterios de aceptación con cada rol. | Cada criterio de `CONTEXTO_PROYECTO.md` se cumple. Pida a Codex anotar el resultado como evidencia. |
| **Inicio de sesión con cuentas reales** | Usted, con su cuenta de desarrollo | Inicie sesión y confirme que ve lo que corresponde a su rol. | Entra y ve las pantallas de su rol. |

Importante: las pruebas automatizadas comprueban el inicio de sesión con **respuestas simuladas** de WAPI_ACCESS. No reemplazan la prueba con una cuenta real. Anote en `CONTEXTO_PROYECTO.md` qué se probó con cuentas reales y qué no.

Para comprobar en pantalla que un rol **no** ve una pantalla o acción, necesita una cuenta real con ese otro rol. Las pruebas automatizadas ya comprueban esa regla en el servidor.

---

## H. Cómo cerrar y retomar una sesión

### Por qué existe `CONTEXTO_PROYECTO.md`

El chat con Codex **no se guarda** entre sesiones. La memoria del proyecto es el archivo `CONTEXTO_PROYECTO.md`, dentro de la carpeta del proyecto. Contiene:

| Sección del archivo | Qué guarda |
|---|---|
| Resumen vigente | Objetivo, estado, trabajo en curso, próxima acción y bloqueo principal, en unas 10 líneas. |
| Proyecto | Nombre, responsable, versión de plantilla, roles, sensibilidad de los datos, alcance. |
| Criterios de aceptación | Qué debe cumplirse y la evidencia de cada uno. |
| Decisiones vigentes | Qué se decidió y por qué. |
| Estado actual | Qué está hecho, qué se probó (con resultado), qué falta y dónde se interrumpió. |
| Pendientes y bloqueos | Qué falta, de quién depende (usted, Codex o IT) y cuándo se da por cerrado. |
| Historial breve | Fecha y una línea por cada solicitud, decisión, avance, prueba o bloqueo. |
| Instrucción para retomar | La frase para empezar en un chat nuevo. |

Codex lo actualiza **durante** el trabajo, no solo al final, porque el RDP puede desconectarse en cualquier momento. Cada respuesta en la que cambió algo debe terminar con una línea:

> Contexto actualizado: <qué anotó>

Si no ve esa línea, pida: *"Actualiza CONTEXTO_PROYECTO.md con lo que acabamos de hacer."*

El archivo **no debe contener** contraseñas, tokens, datos personales ni la copia del chat. Es un resumen para continuar el trabajo.

### Mensaje para cerrar

```text
Guarda el avance, voy a cerrar. Actualiza en CONTEXTO_PROYECTO.md el resumen vigente,
el punto de interrupción, la próxima acción, los pendientes y el historial breve.
Después dime la instrucción para retomar.
```

Resultado esperado: Codex confirma qué anotó y le da la frase para retomar. Luego cierre la ventana negra de la aplicación.

### Mensaje para retomar (en un chat nuevo)

Abra Codex **en la carpeta del proyecto** (`E:\<usuario>\<nombre>`) y escriba:

```text
Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime dónde quedamos y continúa.
```

Resultado esperado: Codex vuelve a preparar el entorno si se perdió (sin tocar su trabajo ni su repositorio Git, si lo tiene), corre la verificación de integridad, le resume en 3 a 5 líneas el estado y propone continuar con la próxima acción. Si le avisa que lo documentado no coincide con los archivos, aclárelo antes de seguir.

---

## I. Qué hacer cuando algo falla

### Tabla de problemas

| Problema | Qué puede comprobar el usuario | Cuándo solicitar ayuda de IT |
|---|---|---|
| **Instalación:** *"No se encontró Python 3.10 o superior."* | Nada más que comprobar. | Siempre: IT debe instalar Python. |
| **Instalación:** error de PowerShell sobre ejecución de scripts deshabilitada | Que el comando incluya `-ExecutionPolicy Bypass`. | Si persiste: IT debe permitirlo o firmar los scripts. |
| **Descarga:** *"No existe el disco E:\. Contacte a IT."* | Que está en el RDP correcto. | Siempre. |
| **Descarga:** *"Ya existe … Elija otro nombre de proyecto."* / *"Nombre no válido"* | Usar otro nombre: letras, números, `-` o `_`, de 3 a 50 caracteres, sin espacios. | No aplica. |
| **Descarga:** *"Usuario no válido"* | Escribir su usuario sin espacios ni tildes; se permiten letras, números, `.`, `-` y `_`. | Si su usuario de Windows no cumple esa regla. |
| **Descarga:** Windows no permite crear la carpeta en `E:\` | Que confirmó el usuario correcto. | Siempre: faltan permisos en el disco. |
| **Descarga:** falla `Invoke-WebRequest` | Que el RDP tenga internet. | Si no hay acceso a GitHub. |
| **Preparación:** *"Esta carpeta está ligada al repositorio de la plantilla…"* | No intente arreglarlo a mano. Cree el proyecto con la descarga de la sección C. | Si no sabe de dónde salió esa carpeta. |
| **Preparación:** advertencia *"El proyecto no está en E:\<usuario>\<proyecto>"* | Dónde quedó la carpeta. | Para moverla de forma segura; Codex no mueve proyectos. |
| **Dependencias:** *"No se pudieron instalar las librerías. Revise la conexión a PyPI o el proxy con IT."* | Volver a intentar una vez. | Si se repite: acceso a PyPI o proxy. |
| **Dependencias:** entorno dañado tras cambiar Python | Pedir a Codex que prepare el entorno con la opción de reinstalar. | Si sigue fallando. |
| **Integridad:** *"La base de seguridad de la plantilla fue modificada."* | Pedir a Codex qué archivos lista y que no los vuelva a tocar. | Para restaurarlos, o si el cambio era necesario (lo decide el equipo dueño). |
| **Pruebas:** *"Hay pruebas que no pasan."* | Pedir a Codex que explique cuál falla y la corrija sin debilitar la seguridad. | Si la prueba es de la plantilla (seguridad, integridad, scripts) y no se corrige sin tocar la zona protegida. |
| **Arranque:** *"El puerto 8501 ya está en uso…"* | Si es su aplicación, recargar el navegador; si no, usar otro puerto (sección G). | No aplica. |
| **Arranque:** *"No se encontró el entorno de la aplicación (.venv)."* | Pedir a Codex: *"Prepara el entorno del proyecto."* | Si la preparación falla. |
| **Arranque:** *"La aplicación se cerró al iniciar…"* o *"…no respondió en 60 segundos"* | Leer el mensaje de la ventana negra, si sigue abierta; probar con otro puerto. | Si se repite. |
| **Configuración:** *"La aplicación está cerrada porque su configuración de seguridad está incompleta."* | Copiar a Codex la lista que aparece debajo. | Si se refiere a valores de producción o HTTPS. |
| **Configuración:** *"…error en PAGINAS de app.py…"* | Pedir a Codex que agregue el permiso faltante en `config/permisos.toml`. | No aplica. |
| **Acceso:** *"Usuario o contraseña incorrectos, o su usuario no tiene acceso a esta aplicación."* | Que escribió bien el usuario y la contraseña. | Si está seguro de la contraseña: IT debe revisar su cuenta en `/DCIU`. |
| **Acceso:** *"El servicio de autenticación no está disponible."* | Que trabaja desde el RDP. Intentar de nuevo en unos minutos. | Si persiste: WAPI_ACCESS no responde. |
| **Acceso:** *"Demasiados intentos fallidos. Intente de nuevo en N minuto(s)."* | Esperar el tiempo indicado. | Si no recuerda su contraseña. |
| **Permisos:** *"Su usuario no tiene un rol con acceso a esta aplicación."* | Pedir a Codex que revise que su rol tenga permisos en `config/permisos.toml`. | Si su cuenta no tiene rol `ADMINISTRADOR` o `USUARIO` en `/DCIU`. |
| **Permisos:** *"No tiene permiso para ver esta página."* o *"…para realizar esta acción."* | Si debería tenerlo, pedir a Codex que revise el permiso del rol. | Si su rol en WAPI_ACCESS no es el correcto. |
| **Sesión:** *"Su sesión venció."* o pide iniciar sesión al recargar | Es normal: 30 minutos sin actividad, 8 horas de sesión o recarga de página. | No aplica. |
| **Datos:** la información capturada desapareció | Es lo esperado al recargar, cerrar la pestaña o la aplicación: no hay almacenamiento permanente en esta etapa. | No aplica; regístrelo como necesidad en `CONTEXTO_PROYECTO.md`. |
| **Funcionamiento:** la pantalla no hace lo que se pidió | Reportarlo con el mensaje de "Reportar un error" (sección F). | Si el error está en el inicio de sesión. |
| **Archivos:** desapareció la carpeta del proyecto o el contexto volvió atrás | Revisar que busca en `E:\<usuario>`. | Siempre: la ubicación no está conservando los archivos. |

### Qué información compartir (y cuál no)

Comparta:

- El texto exacto del mensaje de error.
- Los pasos que hizo, el resultado esperado y el observado.
- El nombre del proyecto, su ruta en `E:\` y la versión de la plantilla (`VERSION`).
- La hora aproximada del problema.
- Capturas de pantalla, revisando que no muestren datos personales de otras personas.

No comparta nunca:

- Contraseñas ni tokens.
- Copias completas de la ventana negra si muestran usuarios de otras personas; copie solo las líneas del error.

---

## J. Cómo solicitar revisión (la publicación es una etapa futura)

Ejecutar la aplicación en el RDP (`localhost`) **no es publicarla**: otras personas no pueden usarla desde ahí. En esta etapa **no existe un procedimiento de publicación**, y usted no debe instalar ni cambiar nada en servidores. **[PENDIENTE: procedimiento y canal de publicación, a definir por IT]**

Lo que sí puede hacer es dejar su proyecto listo para una revisión.

### Cómo preparar el resumen para revisión

Pida a Codex:

```text
Prepara un resumen para revisión a partir de CONTEXTO_PROYECTO.md con:
alcance, criterios de aceptación y su evidencia, funcionalidades terminadas, permisos de cada
rol (ADMINISTRADOR, USUARIO), datos que maneja y su sensibilidad, resultados de las pruebas
automatizadas, qué se probó con cuentas reales y qué no, limitaciones, pendientes y versión
de plantilla. No incluyas contraseñas, tokens ni datos personales.
Antes, corre las pruebas y la verificación de integridad y anota el resultado.
```

Revise que el resumen incluya:

| Elemento | Dónde sale |
|---|---|
| Alcance y criterios de aceptación | `CONTEXTO_PROYECTO.md` → Proyecto y Criterios de aceptación |
| Funcionalidades terminadas | `CONTEXTO_PROYECTO.md` → Estado actual |
| Evidencia de pruebas automatizadas | Resultado de las pruebas (`passed`) y `Plantilla íntegra.`, con fecha |
| Evidencia de pruebas del proceso | Casos probados con cuentas reales de cada rol y su resultado |
| Roles y permisos | `config/permisos.toml` |
| Necesidades futuras | Almacenamiento de datos, otros sistemas, roles nuevos |
| Limitaciones y pendientes | `CONTEXTO_PROYECTO.md` → Pendientes y bloqueos |
| Versión de plantilla | Archivo `VERSION` y fila *Plantilla de origen* |

### Lista de revisión

1. Las pruebas automatizadas pasan completas.
2. Cada pantalla nueva aparece en el menú solo para los roles correctos.
3. Se probó con una cuenta real de otro rol que no ve la pantalla ni puede hacer la acción, o se anotó que falta esa prueba.
4. No hay contraseñas, tokens ni datos personales en el código ni en `CONTEXTO_PROYECTO.md`.
5. `CONTEXTO_PROYECTO.md` está actualizado con lo hecho, lo probado y lo pendiente.

Si comparte la carpeta del proyecto, no incluya `.venv` (se vuelve a crear).

---

## Anexo: responsabilidades en una vista

| Tarea | Usted | Codex | IT / equipo dueño |
|---|---|---|---|
| Describir problema, usuarios, datos y reglas | Sí | Pregunta y resume | — |
| Aprobar alcance y criterios | Sí | Propone | — |
| Confirmar su usuario para la carpeta en `E:\` | Sí | Lo propone | — |
| Descargar y preparar la plantilla en `E:\<usuario>\<nombre>` | Pide | Ejecuta | Da acceso a GitHub, PyPI y Python |
| Construir pantallas, reglas y pruebas | Revisa | Sí | — |
| Asignar permisos a `ADMINISTRADOR` y `USUARIO` | Decide | Lo registra en `config/permisos.toml` | — |
| Crear cuentas de desarrollo y roles nuevos en WAPI_ACCESS | Solicita | Lista los necesarios | IT |
| Probar con cuentas reales | Sí | Anota resultados | Entrega las cuentas |
| Mantener `CONTEXTO_PROYECTO.md` | Revisa | Sí | — |
| Confirmar persistencia y respaldo del disco `E:` | Comprueba en su carpeta | — | IT |
| Habilitar datos u otros sistemas internos | Expresa la necesidad | Registra el pendiente | Etapa futura |
| Cambiar seguridad, diseño o tiempos de sesión | Solicita | No lo hace | Equipo dueño |
| Publicar para otros usuarios | — | — | Etapa futura |
