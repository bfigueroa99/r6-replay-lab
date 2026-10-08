"""Tests de lo que sale de la red: enlaces a trackers y la API de Ubisoft.

Ninguno sale a internet. El cliente recibe el abridor como argumento y la capa
de Django lo toma de `perfil_externo.abrir`, que aca se reemplaza por un
Ubisoft falso que responde lo que cada prueba necesita y anota que le pidieron.
"""

from __future__ import annotations

import base64
import json
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, TestCase

from externo import enlaces, ubisoft
from replays import perfil_externo
from replays.models import PerfilUbisoft, Player

from .factories import make_match, make_round, make_round_player

PID = "A1B2C3D4-0000-4000-8000-0000000000AA"


def _expiracion(horas: float = 3) -> str:
    # el formato real: siete decimales y Z
    vence = datetime.now(UTC) + timedelta(hours=horas)
    return vence.strftime("%Y-%m-%dT%H:%M:%S.1234567Z")


def _login(ticket: str = "tk-1") -> tuple[int, dict]:
    return 200, {"ticket": ticket, "sessionId": "ses-1", "expiration": _expiracion()}


def _perfiles(rank: int = 20, puntos: int = 2950, season: int = 34) -> tuple[int, dict]:
    def tablero(board_id, kills, deaths, wins, losses, abandons=0, rank_id=0, rp=0):
        return {
            "board_id": board_id,
            "full_profiles": [
                {
                    "profile": {
                        "rank": rank_id,
                        "rank_points": rp,
                        "max_rank": rank_id + 1 if rank_id else 0,
                        "max_rank_points": rp + 120 if rp else 0,
                        "season_id": season,
                        "top_rank_position": 0,
                    },
                    "season_statistics": {
                        "kills": kills,
                        "deaths": deaths,
                        "match_outcomes": {"wins": wins, "losses": losses, "abandons": abandons},
                    },
                }
            ],
        }

    return 200, {
        "platform_families_full_profiles": [
            {
                "platform_family": "pc",
                "board_ids_full_profiles": [
                    tablero("ranked", 300, 250, 30, 20, 1, rank_id=rank, rp=puntos),
                    tablero("standard", 90, 100, 8, 12),
                    tablero("event", 0, 0, 0, 0),
                ],
            }
        ]
    }


class FalsoUbisoft:
    """Responde por fragmento de URL, en orden, y guarda cada request."""

    def __init__(self, **rutas):
        self.rutas = {clave: list(respuestas) for clave, respuestas in rutas.items()}
        self.pedidos: list = []

    def __call__(self, request):
        self.pedidos.append(request)
        for fragmento, respuestas in self.rutas.items():
            if fragmento in request.full_url and respuestas:
                status, cuerpo = respuestas.pop(0) if len(respuestas) > 1 else respuestas[0]
                return status, json.dumps(cuerpo).encode() if cuerpo is not None else b""
        raise AssertionError(f"request inesperada: {request.full_url}")

    def contar(self, fragmento: str) -> int:
        return sum(fragmento in r.full_url for r in self.pedidos)


def _ubisoft_sano(**extra) -> FalsoUbisoft:
    rutas = {
        "profiles/sessions": [_login()],
        "full_profiles": [_perfiles()],
        "rewards/public_profile": [(200, {"level": 212, "xp": 1000})],
        "profiles/stats": [
            (200, {"profiles": [{"stats": {"PTotalTimePlayed": {"value": "1800000"}}}]})
        ],
    }
    rutas.update(extra)
    return FalsoUbisoft(**rutas)


# --------------------------------------------------------------------- enlaces


class EnlacesTests(SimpleTestCase):
    def test_con_profile_id_arma_stats_cc_y_r6_tracker(self):
        salida = enlaces.enlaces(PID, "BearF99")
        self.assertEqual([e["sitio"] for e in salida], ["stats.cc", "R6 Tracker"])
        pid = PID.lower()
        self.assertEqual(salida[0]["url"], f"https://stats.cc/siege/BearF99/{pid}")
        self.assertEqual(
            salida[1]["url"], f"https://r6.tracker.network/r6siege/profile/ubi/{pid}/overview"
        )

    def test_un_nick_raro_no_rompe_la_url(self):
        url = enlaces.enlaces(PID, "a b/c")[0]["url"]
        self.assertIn("/siege/a%20b%2Fc/", url)

    def test_sin_profile_id_no_hay_enlaces(self):
        """La ingesta guarda `name:<nick>` cuando el replay no trae id."""
        self.assertEqual(enlaces.enlaces("name:BearF99", "BearF99"), [])
        self.assertEqual(enlaces.enlaces("pid-BearF99", "BearF99"), [])
        self.assertEqual(enlaces.enlaces("", "BearF99"), [])


# --------------------------------------------------------------------- cliente


class SesionTests(SimpleTestCase):
    def test_login_manda_basic_y_el_app_id(self):
        falso = FalsoUbisoft(**{"profiles/sessions": [_login("tk-9")]})
        sesion = ubisoft.iniciar_sesion("yo@example.com", "clave", abrir=falso)

        self.assertEqual(sesion.ticket, "tk-9")
        self.assertEqual(sesion.session_id, "ses-1")
        pedido = falso.pedidos[0]
        self.assertEqual(pedido.get_method(), "POST")
        esperado = base64.b64encode(b"yo@example.com:clave").decode()
        self.assertEqual(pedido.get_header("Authorization"), f"Basic {esperado}")
        self.assertEqual(pedido.get_header("Ubi-appid"), ubisoft.APP_ID)

    def test_clave_mala(self):
        falso = FalsoUbisoft(
            **{"profiles/sessions": [(401, {"httpCode": 401, "message": "Invalid credentials"})]}
        )
        with self.assertRaises(ubisoft.CredencialesInvalidas):
            ubisoft.iniciar_sesion("yo@example.com", "mala", abrir=falso)

    def test_cuenta_con_dos_pasos_lo_dice_claro(self):
        falso = FalsoUbisoft(
            **{"profiles/sessions": [(200, {"twoFactorAuthenticationTicket": "x", "ticket": None})]}
        )
        with self.assertRaises(ubisoft.DosPasos) as caso:
            ubisoft.iniciar_sesion("yo@example.com", "clave", abrir=falso)
        self.assertIn("dos pasos", str(caso.exception))

    def test_demasiados_logins(self):
        falso = FalsoUbisoft(**{"profiles/sessions": [(429, {"httpCode": 429})]})
        with self.assertRaises(ubisoft.Limite):
            ubisoft.iniciar_sesion("yo@example.com", "clave", abrir=falso)

    def test_una_respuesta_que_no_es_json(self):
        def abrir(request):
            return 503, b"<html>mantenimiento</html>"

        with self.assertRaises(ubisoft.ErrorUbisoft) as caso:
            ubisoft.iniciar_sesion("yo@example.com", "clave", abrir=abrir)
        self.assertIn("503", str(caso.exception))

    def test_vigencia_con_margen(self):
        self.assertTrue(ubisoft.Sesion("t", "s", _expiracion(horas=1)).vigente())
        # vence en dos minutos: menos que el margen, no sirve
        self.assertFalse(ubisoft.Sesion("t", "s", _expiracion(horas=2 / 60)).vigente())
        self.assertFalse(ubisoft.Sesion("t", "s", "basura").vigente())


class PerfilClienteTests(SimpleTestCase):
    def setUp(self):
        self.sesion = ubisoft.Sesion("tk-1", "ses-1", _expiracion())

    def test_lee_rango_mmr_y_temporada(self):
        falso = _ubisoft_sano()
        datos = ubisoft.perfil(self.sesion, PID, abrir=falso)

        ranked = datos["tableros"]["ranked"]
        self.assertEqual(ranked["temporada"], "Y9S2")
        self.assertEqual(ranked["rango"], "Oro 1")
        self.assertEqual(ranked["mmr"], 2950)
        self.assertEqual(ranked["rango_maximo"], "Platino 5")
        self.assertEqual(ranked["mmr_maximo"], 3070)
        self.assertEqual(ranked["kd"], 1.2)
        self.assertEqual(ranked["partidas"], 51)
        # el abandono cuenta como partida pero no entra al winrate
        self.assertEqual(ranked["winrate"], 60.0)
        self.assertEqual(datos["nivel"], 212)
        self.assertEqual(datos["horas"], 500)

    def test_las_consultas_llevan_el_ticket(self):
        falso = _ubisoft_sano()
        ubisoft.perfil(self.sesion, PID, abrir=falso)
        for pedido in falso.pedidos:
            self.assertEqual(pedido.get_header("Authorization"), "Ubi_v1 t=tk-1")
            self.assertEqual(pedido.get_header("Ubi-sessionid"), "ses-1")
        self.assertIn(PID.lower(), falso.pedidos[0].full_url)

    def test_sin_muertes_no_hay_kd(self):
        datos = ubisoft.perfil(self.sesion, PID, abrir=_ubisoft_sano())
        self.assertIsNone(datos["tableros"]["event"]["kd"])
        self.assertIsNone(datos["tableros"]["event"]["winrate"])

    def test_nivel_y_horas_son_opcionales(self):
        falso = _ubisoft_sano(
            **{
                "rewards/public_profile": [(404, {"httpCode": 404})],
                "profiles/stats": [(500, {"httpCode": 500, "message": "boom"})],
            }
        )
        datos = ubisoft.perfil(self.sesion, PID, abrir=falso)
        self.assertEqual(datos["tableros"]["ranked"]["rango"], "Oro 1")
        self.assertIsNone(datos["nivel"])
        self.assertIsNone(datos["horas"])

    def test_ticket_vencido(self):
        falso = _ubisoft_sano(full_profiles=[(401, {"httpCode": 401})])
        with self.assertRaises(ubisoft.SesionVencida):
            ubisoft.perfil(self.sesion, PID, abrir=falso)

    def test_sin_temporada_es_un_error_y_no_ceros(self):
        falso = _ubisoft_sano(full_profiles=[(200, {"platform_families_full_profiles": []})])
        with self.assertRaises(ubisoft.ErrorUbisoft):
            ubisoft.perfil(self.sesion, PID, abrir=falso)

    def test_nombres_de_rango_y_temporada(self):
        self.assertEqual(ubisoft.nombre_rango(0), "Sin rango")
        self.assertEqual(ubisoft.nombre_rango(1), "Cobre 5")
        self.assertEqual(ubisoft.nombre_rango(35), "Diamante 1")
        self.assertEqual(ubisoft.nombre_rango(36), "Campeones")
        self.assertEqual(ubisoft.nombre_rango(40), "Rango 40")
        self.assertIsNone(ubisoft.nombre_rango(None))
        self.assertEqual(ubisoft.codigo_temporada(1), "Y1S1")
        self.assertEqual(ubisoft.codigo_temporada(40), "Y10S4")
        self.assertIsNone(ubisoft.codigo_temporada(0))


# --------------------------------------------------------------------- Django


class _ConUbisoft(TestCase):
    """Credenciales de mentira y el archivo de sesion en una carpeta temporal."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        ajustes = self.settings(
            UBI_EMAIL="yo@example.com",
            UBI_PASSWORD="clave",
            UBI_SESION_PATH=self.tmp / "sesion.json",
        )
        ajustes.enable()
        self.addCleanup(ajustes.disable)

        match = make_match(index=0)
        rnd = make_round(match, 0)
        make_round_player(rnd)
        make_round_player(rnd, username="amigo", is_me=False, team_index=0)
        self.amigo = Player.objects.get(username="amigo")
        self.amigo.profile_id = PID
        self.amigo.save()

    def con(self, falso):
        return mock.patch.object(perfil_externo, "abrir", falso)

    def consultar(self, player=None):
        player = player or self.amigo
        return self.client.post(f"/api/players/{player.id}/ubisoft/")


class PerfilJugadorTests(_ConUbisoft):
    def test_abrir_el_perfil_trae_los_enlaces_y_no_sale_a_la_red(self):
        def prohibido(request):
            raise AssertionError("abrir un perfil no puede consultar a Ubisoft")

        with self.con(prohibido):
            data = self.client.get(f"/api/players/{self.amigo.id}/").json()

        externo = data["externo"]
        self.assertEqual([e["sitio"] for e in externo["enlaces"]], ["stats.cc", "R6 Tracker"])
        self.assertTrue(externo["ubisoft"]["configurado"])
        self.assertTrue(externo["ubisoft"]["consultable"])
        self.assertIsNone(externo["ubisoft"]["datos"])

    def test_sin_credenciales_lo_dice(self):
        with self.settings(UBI_EMAIL="", UBI_PASSWORD=""):
            data = self.client.get(f"/api/players/{self.amigo.id}/").json()
            self.assertFalse(data["externo"]["ubisoft"]["configurado"])
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("UBI_EMAIL", respuesta.json()["error"])

    def test_jugador_sin_profile_id(self):
        yo = Player.objects.get(is_me=True)
        yo.profile_id = "name:BearF99"
        yo.save()
        data = self.client.get(f"/api/players/{yo.id}/").json()
        self.assertEqual(data["externo"]["enlaces"], [])
        self.assertFalse(data["externo"]["ubisoft"]["consultable"])
        self.assertEqual(self.consultar(yo).status_code, 400)

    def test_consulta_guarda_y_el_perfil_la_muestra(self):
        with self.con(_ubisoft_sano()):
            respuesta = self.consultar()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["datos"]["tableros"]["ranked"]["rango"], "Oro 1")
        self.assertIsNotNone(respuesta.json()["consultado"])
        self.assertEqual(PerfilUbisoft.objects.get(player=self.amigo).datos["nivel"], 212)

        # lo guardado se ve al abrir el perfil, sin volver a consultar
        data = self.client.get(f"/api/players/{self.amigo.id}/").json()
        self.assertEqual(data["externo"]["ubisoft"]["datos"]["tableros"]["ranked"]["mmr"], 2950)

    def test_reconsultar_pisa_el_anterior(self):
        with self.con(_ubisoft_sano()):
            self.consultar()
        with self.con(_ubisoft_sano(full_profiles=[_perfiles(rank=21, puntos=3010)])):
            self.consultar()
        self.assertEqual(PerfilUbisoft.objects.count(), 1)
        self.assertEqual(
            PerfilUbisoft.objects.get().datos["tableros"]["ranked"]["rango"], "Platino 5"
        )

    def test_un_error_de_ubisoft_llega_a_la_ui_y_no_guarda_nada(self):
        falso = FalsoUbisoft(
            **{"profiles/sessions": [(401, {"httpCode": 401, "message": "Invalid credentials"})]}
        )
        with self.con(falso):
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 502)
        self.assertIn("contraseña", respuesta.json()["error"])
        self.assertFalse(PerfilUbisoft.objects.exists())

    def test_sin_red(self):
        def caido(request):
            raise ubisoft.SinConexion("No pude conectar con Ubisoft: sin red")

        with self.con(caido):
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 502)
        self.assertIn("No pude conectar", respuesta.json()["error"])

    def test_la_cabecera_sabe_quien_eres_y_si_hay_ubisoft(self):
        data = self.client.get("/api/health/").json()
        self.assertEqual(data["player_id"], Player.objects.get(is_me=True).id)
        self.assertTrue(data["ubisoft_configurado"])


class SesionGuardadaTests(_ConUbisoft):
    def test_la_segunda_consulta_reusa_el_ticket(self):
        """Ubisoft corta la IP con pocos logins: uno por ticket, no por consulta."""
        falso = _ubisoft_sano()
        with self.con(falso):
            self.consultar()
            self.consultar()
        self.assertEqual(falso.contar("profiles/sessions"), 1)
        self.assertEqual(falso.contar("full_profiles"), 2)
        guardada = json.loads((self.tmp / "sesion.json").read_text(encoding="utf-8"))
        self.assertEqual(guardada["ticket"], "tk-1")
        self.assertNotIn("clave", json.dumps(guardada))

    def guardar(self, ticket: str, cuenta: str = "yo@example.com"):
        datos = {"cuenta": cuenta, "ticket": ticket, "session_id": "x", "expiracion": _expiracion()}
        (self.tmp / "sesion.json").write_text(json.dumps(datos), encoding="utf-8")

    def test_ticket_guardado_muerto_hace_un_login_nuevo_y_reintenta(self):
        self.guardar("tk-viejo")
        falso = _ubisoft_sano(
            **{
                "profiles/sessions": [_login("tk-nuevo")],
                "full_profiles": [(401, {"httpCode": 401}), _perfiles()],
            }
        )
        with self.con(falso):
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(falso.contar("profiles/sessions"), 1)
        ultimo = [p for p in falso.pedidos if "full_profiles" in p.full_url][-1]
        self.assertEqual(ultimo.get_header("Authorization"), "Ubi_v1 t=tk-nuevo")

    def test_un_ticket_recien_emitido_rechazado_no_entra_en_bucle(self):
        falso = _ubisoft_sano(full_profiles=[(401, {"httpCode": 401})])
        with self.con(falso):
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 502)
        self.assertIn("sesión nueva", respuesta.json()["error"])
        self.assertEqual(falso.contar("profiles/sessions"), 1)

    def test_ticket_de_otra_cuenta_no_se_usa(self):
        self.guardar("ajeno", cuenta="otra@example.com")
        falso = _ubisoft_sano()
        with self.con(falso):
            self.consultar()
        self.assertEqual(falso.contar("profiles/sessions"), 1)
        self.assertNotIn("ajeno", json.dumps([p.headers for p in falso.pedidos]))
