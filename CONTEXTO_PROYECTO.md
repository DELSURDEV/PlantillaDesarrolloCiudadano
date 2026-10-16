# Contexto del proyecto
Sin contraseñas, tokens, secretos ni datos personales.

## Resumen vigente
- Proyecto y objetivo: {{NOMBRE_PROYECTO}} — <objetivo pendiente de definir con el usuario>
- Estado: creado desde la plantilla, sin funcionalidad propia
- Trabajo en curso: ninguno
- Próxima acción: definir con el usuario el objetivo, los usuarios y los roles
- Bloqueo principal: datos de Entra ID de IT (tenant, client ID, secreto, roles)
- Seguridad y SSO: base de la plantilla {{VERSION_PLANTILLA}} · aprobación de IT: pendiente
- Última actualización: {{FECHA}}

## Proyecto
| Campo | Valor |
|---|---|
| Nombre y responsable | {{NOMBRE_PROYECTO}} · <responsable> |
| Plantilla de origen | {{VERSION_PLANTILLA}} (copia desligada, sin Git de la plantilla) |
| Usuarios y roles de Entra ID | <pendiente> |
| Datos y sensibilidad | <pendiente> |
| Incluido / fuera de alcance | <pendiente> |
| Ruta | {{RUTA_PROYECTO}} |

## Criterios de aceptación
| ID | Criterio | Estado y evidencia |
|---|---|---|

## Decisiones vigentes
| Tema | Decisión | Motivo u origen |
|---|---|---|
| Base | Plantilla Streamlit con SSO {{VERSION_PLANTILLA}} | Estándar del equipo |

## Estado actual
- Implementado: aplicación vacía de la plantilla (página Inicio con bienvenida)
- Probado (comando y resultado): no probado
- Pendiente: todo lo propio del proyecto
- Punto de interrupción (archivo, último paso, siguiente paso): —

## Pendientes y bloqueos
| ID | Prioridad | Descripción | Responsable (usuario / Codex / IT) | Cuándo se da por cerrado |
|---|---|---|---|---|
| P1 | Alta | Registro de la app en Entra ID, roles y secreto | IT | Inicio de sesión funciona en http://localhost:8501 |

## Comandos para ejecutar y probar
```powershell
Start-Process -FilePath .\.venv\Scripts\streamlit.exe -ArgumentList "run", "app.py"   # abre http://localhost:8501
.\.venv\Scripts\python.exe -m pytest      # pruebas
```

## Historial breve
| Fecha | Tipo | Solicitud, decisión, avance o bloqueo |
|---|---|---|
| {{FECHA}} | Creación | Proyecto creado desde la plantilla {{VERSION_PLANTILLA}} |

## Instrucción para retomar
> Lee AGENTS.md y CONTEXTO_PROYECTO.md, dime en pocas líneas dónde quedamos y continúa con la próxima acción.
