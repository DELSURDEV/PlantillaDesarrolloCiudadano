"""Pruebas de la base de seguridad. Protegidas: no modificar."""

from __future__ import annotations

import time
try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from unittest import mock

import pytest
from streamlit.testing.v1 import AppTest

from conftest import RAIZ
from seguridad import autorizacion
from seguridad.configuracion import ErrorConfiguracion, cargar_configuracion
from seguridad.identidad import IdentidadRechazada, RegistroActividad, validar_identidad

TENANT = "11111111-2222-3333-4444-555555555555"
CLIENTE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
OID = "99999999-8888-7777-6666-555555555555"
ROLES = {"roles": {"Usuario": ["inicio:ver"], "Administrador": ["inicio:ver", "reportes:ver"]}}


def secretos(**cambios_auth):
    auth = {
        "redirect_uri": "http://localhost:8501/oauth2callback",
        "cookie_secret": "x" * 40,
        "client_id": CLIENTE,
        "client_secret": "secreto-de-prueba",
        "server_metadata_url": (
            f"https://login.microsoftonline.com/{TENANT}/v2.0/.well-known/openid-configuration"
        ),
    }
    auth.update(cambios_auth)
    auth = {k: v for k, v in auth.items() if v is not None}
    return {"auth": auth, "seguridad": {"ambiente": "desarrollo"}}


def reclamaciones(**cambios):
    datos = {
        "is_logged_in": True,
        "tid": TENANT,
        "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
        "aud": CLIENTE,
        "oid": OID,
        "iat": int(time.time()) - 60,
        "name": "Ana Prueba",
        "preferred_username": "ana@empresa.test",
        "roles": ["Usuario"],
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def config():
    return cargar_configuracion(secretos(), ROLES)


# --- Configuración ------------------------------------------------------------


def test_configuracion_valida(config):
    assert config.tenant_id == TENANT
    assert config.sesion_max_s == 8 * 3600


def test_permisos_toml_de_la_plantilla_es_valido():
    datos = tomllib.loads((RAIZ / "config" / "permisos.toml").read_text(encoding="utf-8"))
    cargar_configuracion(secretos(), datos)


@pytest.mark.parametrize(
    ("cambios", "fragmento"),
    [
        ({"client_id": None}, "client_id"),
        ({"client_secret": "<CLIENT_SECRET>"}, "client_secret"),
        ({"cookie_secret": "corto"}, "32 caracteres"),
        ({"client_id": "no-es-guid"}, "GUID"),
        (
            {"server_metadata_url": "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"},
            "common",
        ),
        (
            {"server_metadata_url": "https://login.malicioso.test/x/v2.0/.well-known/openid-configuration"},
            "server_metadata_url",
        ),
        ({"redirect_uri": "http://app.empresa.test/oauth2callback"}, "HTTPS"),
        ({"redirect_uri": "http://localhost:8501/otra"}, "/oauth2callback"),
        ({"expose_tokens": ["id", "access"]}, "no permitidas"),
        ({"microsoft": {"client_id": "x"}}, "no permitidas"),
    ],
)
def test_configuracion_insegura_se_rechaza(cambios, fragmento):
    with pytest.raises(ErrorConfiguracion) as info:
        cargar_configuracion(secretos(**cambios), ROLES)
    assert any(fragmento in p for p in info.value.problemas), info.value.problemas
    assert "secreto-de-prueba" not in str(info.value)


def test_produccion_exige_https():
    valores = secretos()
    valores["seguridad"]["ambiente"] = "produccion"
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(valores, ROLES)


def test_sin_auth_y_sin_roles():
    with pytest.raises(ErrorConfiguracion) as info:
        cargar_configuracion({"seguridad": {"ambiente": "desarrollo"}}, {"roles": {}})
    assert any("[auth]" in p for p in info.value.problemas)
    assert any("al menos un rol" in p for p in info.value.problemas)


def test_permiso_con_formato_invalido():
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(secretos(), {"roles": {"Usuario": ["Ver Todo"]}})


# --- Identidad ----------------------------------------------------------------


def test_identidad_valida(config):
    usuario = validar_identidad(reclamaciones(), config, time.time())
    assert usuario.oid == OID
    assert usuario.permisos == {"inicio:ver"}


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"is_logged_in": False}, "sin_sesion"),
        ({"tid": "00000000-0000-0000-0000-000000000000"}, "tenant_no_permitido"),
        ({"iss": "https://login.microsoftonline.com/otro/v2.0"}, "emisor_no_valido"),
        ({"aud": "otra-app"}, "audiencia_no_valida"),
        ({"oid": ""}, "oid_no_valido"),
        ({"iat": None}, "sin_fecha_inicio"),
        ({"iat": int(time.time()) + 3600}, "fecha_inicio_futura"),
        ({"iat": int(time.time()) - 9 * 3600}, "sesion_vencida"),
    ],
)
def test_identidad_rechazada(config, cambios, motivo):
    with pytest.raises(IdentidadRechazada) as info:
        validar_identidad(reclamaciones(**cambios), config, time.time())
    assert info.value.motivo == motivo


def test_rol_desconocido_no_da_permisos(config):
    usuario = validar_identidad(reclamaciones(roles=["SuperUsuario"]), config, time.time())
    assert usuario.permisos == frozenset()


def test_inactividad_cierra_la_sesion_en_todas_las_pestanas(config):
    registro = RegistroActividad()
    ahora = time.time()
    usuario = validar_identidad(reclamaciones(), config, ahora)
    assert registro.registrar(usuario, config, ahora) is True
    assert registro.registrar(usuario, config, ahora + 60) is False
    with pytest.raises(IdentidadRechazada):
        registro.registrar(usuario, config, ahora + 60 + config.inactividad_s + 1)
    with pytest.raises(IdentidadRechazada):  # la misma cookie no vuelve a servir
        registro.registrar(usuario, config, ahora + config.inactividad_s + 70)


# --- Aplicación completa ------------------------------------------------------


def ejecutar(reclamaciones_usuario, valores=None):
    autorizacion._registro_actividad.clear()
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    for seccion, contenido in (valores or secretos()).items():
        app.secrets[seccion] = contenido
    with (
        mock.patch.object(autorizacion, "_leer_reclamaciones", return_value=reclamaciones_usuario),
        mock.patch.object(autorizacion.st, "login") as login,
        mock.patch.object(autorizacion.st, "logout") as logout,
    ):
        app.run()
    return app, login, logout


def textos(app):
    return " ".join(e.value for e in [*app.title, *app.markdown, *app.error, *app.info])


def test_sin_sesion_muestra_solo_inicio_de_sesion():
    app, login, _ = ejecutar({"is_logged_in": False})
    assert "Bienvenido" not in textos(app)
    assert [b.label for b in app.button] == ["Iniciar sesión con Microsoft"]
    assert len(app.sidebar) == 0  # sin menú antes de iniciar sesión
    login.assert_not_called()


def test_usuario_con_rol_entra_a_inicio():
    app, _, logout = ejecutar(reclamaciones())
    assert "Bienvenido, Ana Prueba" in textos(app)
    logout.assert_not_called()


def test_exigir_permiso_en_servicios(config):
    from seguridad import PermisoDenegado

    usuario = validar_identidad(reclamaciones(), config, time.time())
    usuario.exigir("inicio:ver")
    with pytest.raises(PermisoDenegado):
        usuario.exigir("facturas:aprobar")


def test_otro_tenant_cierra_sesion():
    app, _, logout = ejecutar(reclamaciones(tid="00000000-0000-0000-0000-000000000000"))
    logout.assert_called_once()
    assert "Bienvenido" not in textos(app)


def test_sin_roles_no_entra():
    app, _, _ = ejecutar(reclamaciones(roles=[]))
    assert "no tiene un rol asignado" in textos(app)
    assert "Bienvenido" not in textos(app)


def test_configuracion_incompleta_cierra_la_app():
    app, _, _ = ejecutar(reclamaciones(), secretos(client_secret=None))
    assert "está cerrada" in textos(app)
    assert "Bienvenido" not in textos(app)


def test_boton_de_acceso_inicia_sesion_con_microsoft():
    autorizacion._registro_actividad.clear()
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    for seccion, contenido in secretos().items():
        app.secrets[seccion] = contenido
    with (
        mock.patch.object(autorizacion, "_leer_reclamaciones", return_value={"is_logged_in": False}),
        mock.patch.object(autorizacion.st, "login") as login,
    ):
        app.run()
        app.button[0].click().run()
    login.assert_called_once()
