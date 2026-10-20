"""Pruebas de la base de seguridad (login WAPI_ACCESS). Protegidas: no modificar."""

from __future__ import annotations

import json
import time
from unittest import mock

import httpx
import pytest
from streamlit.testing.v1 import AppTest

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from conftest import RAIZ
from seguridad import autorizacion, configuracion, wapi
from seguridad.configuracion import ErrorConfiguracion, cargar_configuracion
from seguridad.identidad import ControlIntentos, PermisoDenegado, SesionVencida, crear_usuario, verificar_vigencia

ROLES = {"roles": {"Administrador": ["inicio:ver", "reportes:ver"], "Usuario": ["inicio:ver"]}}
URL = configuracion.URL_LOGIN_WAPI
APP = configuracion.APLICACION_WAPI


def secretos(**cambios_wapi):
    datos = {"tiempo_espera_s": 5}
    datos.update(cambios_wapi)
    datos = {k: v for k, v in datos.items() if v is not None}
    return {"wapi": datos, "seguridad": {"ambiente": "desarrollo"}}


def respuesta_wapi(roles=("ADMINISTRADOR",), rutas=("/Inicio/Principal",), **extra):
    sitemaps = [{"id": 0, "title": "APP", "description": "Inicio", "url": "", "parent": ""}]
    sitemaps.append({"id": 1, "title": "Operación", "description": "", "url": "", "parent": "0"})
    for indice, ruta in enumerate(rutas, start=10):
        sitemaps.append({"id": indice, "title": f"Página {indice}", "description": "", "url": ruta, "parent": "1"})
    datos = {"userData": {"userName": "AGarcia", "displayName": "Ana García", "roles": list(roles), "sitemaps": sitemaps}}
    datos.update(extra)
    return datos


@pytest.fixture
def config():
    return cargar_configuracion(secretos(), ROLES)


# --- Configuración ------------------------------------------------------------


def test_configuracion_valida(config):
    assert config.aplicacion == "/DCIU"
    assert config.url_login == "http://192.168.132.1/WAPI_ACCESS/api/v2/Auth/login"
    assert config.roles_permisos["ADMINISTRADOR"] == {"inicio:ver", "reportes:ver"}


def test_permisos_toml_de_la_plantilla_es_valido():
    datos = tomllib.loads((RAIZ / "config" / "permisos.toml").read_text(encoding="utf-8"))
    cargar_configuracion(secretos(), datos)


def test_ejemplo_de_secrets_no_tiene_secretos():
    texto = (RAIZ / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8").lower()
    for palabra in ("password", "contrasena", "client_secret", "token", "cookie_secret"):
        assert f"{palabra} =" not in texto


@pytest.mark.parametrize(
    ("cambios", "fragmento"),
    [
        ({"url_login": "https://otro.servidor.test/login"}, "son fijos de la plantilla"),
        ({"aplicacion": "/OTRA"}, "son fijos de la plantilla"),
        ({"tiempo_espera_s": 120}, "tiempo_espera_s"),
        ({"token": "x"}, "no permitidas"),
    ],
)
def test_configuracion_insegura_se_rechaza(cambios, fragmento):
    with pytest.raises(ErrorConfiguracion) as info:
        cargar_configuracion(secretos(**cambios), ROLES)
    assert any(fragmento in p for p in info.value.problemas), info.value.problemas


def test_produccion_exige_https_o_excepcion_registrada():
    valores = secretos()
    valores["seguridad"]["ambiente"] = "produccion"
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(valores, ROLES)
    valores["wapi"].update(permitir_http=True, referencia_excepcion_http="TICKET-123")
    assert cargar_configuracion(valores, ROLES).es_produccion


def test_sin_seccion_wapi_usa_valores_fijos_y_exige_roles():
    assert cargar_configuracion({"seguridad": {"ambiente": "desarrollo"}}, ROLES).aplicacion == "/DCIU"
    with pytest.raises(ErrorConfiguracion) as info:
        cargar_configuracion({"seguridad": {"ambiente": "desarrollo"}}, {"roles": {}})
    assert any("al menos un rol" in p for p in info.value.problemas)


def test_ejemplo_de_secrets_es_valido():
    datos = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8"))
    assert cargar_configuracion(datos, ROLES).ambiente == "desarrollo"


# --- Cliente WAPI_ACCESS --------------------------------------------------------


def cliente_simulado(estado=200, cuerpo=None, error=None, capturar=None):
    def responder(peticion):
        if capturar is not None:
            capturar.append(peticion)
        if error:
            raise error
        contenido = cuerpo if isinstance(cuerpo, (bytes, str)) else json.dumps(cuerpo)
        return httpx.Response(estado, content=contenido)

    return httpx.Client(transport=httpx.MockTransport(responder))


def test_login_correcto_envia_usuario_y_aplicacion(config):
    peticiones = []
    resultado = wapi.autenticar(config, " AGarcia ", "clave", cliente_simulado(200, respuesta_wapi(), capturar=peticiones))
    assert resultado.usuario == "AGarcia"
    assert resultado.roles == ("ADMINISTRADOR",)
    enviado = json.loads(peticiones[0].content)
    assert enviado == {"username": "AGarcia", "password": "clave", "app": APP}
    assert str(peticiones[0].url) == URL


def test_la_respuesta_no_conserva_tokens(config):
    datos = respuesta_wapi(token="eyJ-secreto", refreshToken="otro")
    resultado = wapi.autenticar(config, "AGarcia", "clave", cliente_simulado(200, datos))
    assert "eyJ" not in repr(resultado)


@pytest.mark.parametrize("estado", [400, 401, 403])
def test_credenciales_invalidas(config, estado):
    with pytest.raises(wapi.CredencialesInvalidas):
        wapi.autenticar(config, "AGarcia", "mala", cliente_simulado(estado, {"message": "error"}))


@pytest.mark.parametrize(
    ("estado", "cuerpo", "error"),
    [
        (500, {"x": 1}, None),
        (404, {"x": 1}, None),
        (200, "<html>no es json</html>", None),
        (200, None, httpx.ConnectTimeout("tiempo agotado")),
        (200, {"userData": {"userName": "x", "roles": "ADMIN"}}, None),
    ],
)
def test_servicio_no_disponible_falla_cerrado(config, estado, cuerpo, error):
    with pytest.raises(wapi.ServicioNoDisponible):
        wapi.autenticar(config, "AGarcia", "clave", cliente_simulado(estado, cuerpo, error))


@pytest.mark.parametrize("cuerpo", [{}, {"userData": None}, {"userData": {"userName": ""}}, []])
def test_respuesta_200_sin_usuario_no_deja_entrar(config, cuerpo):
    with pytest.raises(wapi.CredencialesInvalidas):
        wapi.autenticar(config, "AGarcia", "clave", cliente_simulado(200, cuerpo))


@pytest.mark.parametrize(("usuario", "clave"), [("", "x"), ("a", ""), ("a" * 200, "x"), ("a", "x" * 300)])
def test_entradas_invalidas_no_llaman_al_servicio(config, usuario, clave):
    peticiones = []
    with pytest.raises(wapi.CredencialesInvalidas):
        wapi.autenticar(config, usuario, clave, cliente_simulado(200, respuesta_wapi(), capturar=peticiones))
    assert peticiones == []


# --- Usuario, permisos, sesión e intentos ---------------------------------------


def test_la_respuesta_solo_conserva_usuario_nombre_y_roles(config):
    resultado = wapi.interpretar_respuesta(respuesta_wapi())
    assert set(vars(resultado)) == {"usuario", "nombre", "roles"}


def test_sitemaps_con_formato_raro_se_ignoran(config):
    datos = respuesta_wapi()
    datos["userData"]["sitemaps"] = "cualquier cosa"
    assert wapi.interpretar_respuesta(datos).roles == ("ADMINISTRADOR",)


def test_permisos_desde_los_roles(config):
    usuario = crear_usuario(wapi.interpretar_respuesta(respuesta_wapi()), config, time.time())
    assert usuario.id == "agarcia"
    assert usuario.permisos == {"inicio:ver", "reportes:ver"}
    usuario.exigir("reportes:ver")
    with pytest.raises(PermisoDenegado):
        usuario.exigir("facturas:aprobar")


def test_rol_desconocido_no_da_permisos(config):
    usuario = crear_usuario(wapi.interpretar_respuesta(respuesta_wapi(roles=("INVITADO",))), config, time.time())
    assert usuario.permisos == frozenset()


def test_vigencia_de_la_sesion(config):
    ahora = time.time()
    verificar_vigencia(ahora - 60, ahora - 60, config, ahora)
    with pytest.raises(SesionVencida):
        verificar_vigencia(ahora - 60, ahora - config.inactividad_s - 1, config, ahora)
    with pytest.raises(SesionVencida):
        verificar_vigencia(ahora - config.sesion_max_s - 1, ahora, config, ahora)


def test_bloqueo_por_intentos_fallidos(config):
    control = ControlIntentos()
    ahora = time.time()
    for _ in range(config.intentos_maximos):
        assert control.segundos_bloqueado("AGarcia", config, ahora) == 0
        control.registrar_fallo("agarcia", ahora)
    assert control.segundos_bloqueado("AGARCIA", config, ahora) > 0
    assert control.segundos_bloqueado("AGarcia", config, ahora + config.bloqueo_s + 1) == 0


# --- Aplicación completa ------------------------------------------------------


def ejecutar_app(respuesta=None, error=None, valores=None, credenciales=("AGarcia", "clave")):
    """Corre app.py, completa el formulario de acceso y devuelve (app, mock de WAPI)."""
    autorizacion._control_intentos.clear()
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    for seccion, contenido in (valores or secretos()).items():
        app.secrets[seccion] = contenido
    with mock.patch.object(autorizacion, "_autenticar_wapi") as falso:
        if error is not None:
            falso.side_effect = error
        else:
            falso.return_value = wapi.interpretar_respuesta(respuesta or respuesta_wapi())
        app.run()
        if credenciales and app.text_input:
            app.text_input[0].input(credenciales[0])
            app.text_input[1].input(credenciales[1])
            app.button[0].click().run()
    return app, falso


def textos(app):
    return " ".join(e.value for e in [*app.title, *app.markdown, *app.error, *app.info])


def test_sin_sesion_muestra_solo_el_formulario():
    app, falso = ejecutar_app(credenciales=None)
    assert [t.label for t in app.text_input] == ["Usuario", "Contraseña"]
    assert app.text_input[1].proto.type == app.text_input[1].proto.PASSWORD
    assert "Bienvenido" not in textos(app)
    assert len(app.sidebar) == 0
    falso.assert_not_called()


def test_login_correcto_entra_a_inicio():
    app, falso = ejecutar_app()
    falso.assert_called_once()
    assert "Bienvenido, Ana García" in textos(app)


def test_credenciales_invalidas_no_entra():
    app, _ = ejecutar_app(error=wapi.CredencialesInvalidas())
    assert autorizacion.MENSAJE_CREDENCIALES in textos(app)
    assert "Bienvenido" not in textos(app)


def test_servicio_caido_no_entra():
    app, _ = ejecutar_app(error=wapi.ServicioNoDisponible("caido"))
    assert autorizacion.MENSAJE_SERVICIO in textos(app)
    assert "Bienvenido" not in textos(app)


def test_sin_rol_conocido_no_entra():
    app, _ = ejecutar_app(respuesta=respuesta_wapi(roles=("INVITADO",)))
    assert "no tiene un rol con acceso" in textos(app)
    assert "Bienvenido" not in textos(app)


def test_configuracion_incompleta_cierra_la_app():
    valores = secretos()
    valores["seguridad"]["ambiente"] = "pruebas"
    app, falso = ejecutar_app(valores=valores, credenciales=None)
    assert "está cerrada" in textos(app)
    assert not app.text_input
    falso.assert_not_called()
