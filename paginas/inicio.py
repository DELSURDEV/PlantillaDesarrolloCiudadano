from interfaz import encabezado
from seguridad import requerir_permiso

usuario = requerir_permiso("inicio:ver")

encabezado(
    "Inicio",
    descripcion=f"Bienvenido, {usuario.nombre}.",
    antetitulo="Página principal",
    icono="home",
)
