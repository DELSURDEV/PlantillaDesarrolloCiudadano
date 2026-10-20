"""Punto de entrada. Ejecutar con: streamlit run app.py

Cada página nueva se registra en PAGINAS con su permiso y su grupo del menú.
Solo se muestran las páginas cuyo permiso tiene alguno de los roles del usuario.
"""

from interfaz import Aplicacion, ejecutar_aplicacion
from seguridad import Pagina

APLICACION = Aplicacion(
    nombre="Nueva aplicación",  # Cambiar por el nombre del proyecto.
    modulo="DELSUR",
    descripcion="Aplicación de desarrollo ciudadano.",
    version="0.1.0",
)

PAGINAS = [
    Pagina("paginas/inicio.py", "Inicio", "inicio:ver", ":material/home:", grupo="General"),
]

ejecutar_aplicacion(APLICACION, PAGINAS)
