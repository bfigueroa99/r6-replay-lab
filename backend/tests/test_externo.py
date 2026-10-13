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


def _fila(nombre, rondas, ganadas, bajas, muertes, headshots, partidas=10) -> dict:
    """Una fila de `playerstats` con los conteos y un ratio armado que no cuadra.

    El `killDeathRatio` de mentira esta para probar que el K/D sale de los
    conteos, que es lo que lo hace comparable con el de los replays.
    """
    return {
        "statsDetail": nombre,
        "matchesPlayed": partidas,
        "roundsPlayed": rondas,
        "roundsWon": ganadas,
        "roundsLost": rondas - ganadas,
        "kills": bajas,
        "death": muertes,
        "headshots": headshots,
        "killDeathRatio": {"value": 9.99},
    }


def _playerstats(modos: dict, **extra) -> tuple[int, dict]:
    return 200, {
        "platforms": {"PC": {"gameModes": modos}},
        "startDate": "20260601",
        "endDate": "20260930",
        **extra,
    }


def _operadores() -> tuple[int, dict]:
    return _playerstats(
        {
            "ranked": {
                "type": "ranked",
                "teamRoles": {
                    "all": [_fila("Ash", 999, 1, 1, 1, 1)],
                    "Attacker": [_fila("Ash", 120, 66, 96, 80, 48), _fila("IQ", 0, 0, 0, 0, 0)],
                    "Defender": [_fila("Jäger", 100, 52, 70, 70, 28)],
                },
            },
            "casual": {"teamRoles": {"Attacker": [], "Defender": []}},
        }
    )


def _mapas() -> tuple[int, dict]:
    return _playerstats(
        {
            "ranked": {
                "teamRoles": {
                    "all": [
                        _fila("CLUBHOUSE", 90, 40, 70, 75, 30, partidas=12),
                        _fila("KAFE DOSTOYEVSKY", 30, 12, 20, 0, 0, partidas=4),
                    ],
                    "Attacker": [_fila("CLUBHOUSE", 45, 15, 30, 40, 12)],
                    "Defender": [_fila("CLUBHOUSE", 45, 25, 40, 35, 18)],
                }
            }
        }
    )


def _arma(nombre, rondas, ganadas, bajas, headshots) -> dict:
    return {
        "weaponName": nombre,
        "roundsPlayed": rondas,
        "roundsWon": ganadas,
        "kills": bajas,
        "headshots": headshots,
    }


def _armas() -> tuple[int, dict]:
    def ranura(*tipos):
        return {"weaponTypes": [{"weaponType": t, "weapons": armas} for t, armas in tipos]}

    return _playerstats(
        {
            "ranked": {
                "teamRoles": {
                    "all": {
                        "weaponSlots": {
                            "primaryWeapons": ranura(
                                ("Assault Rifle", [_arma("R4-C", 120, 66, 90, 45)]),
                                # el segundo tipo es el que siegeapi no lee
                                ("Submachine Gun", [_arma("MP5", 100, 52, 64, 24)]),
                            ),
                            "secondaryWeapons": ranura(
                                ("Handgun", [_arma("5.7 USG", 40, 20, 0, 0), _arma("P9", 0, 0, 0, 0)])
                            ),
                        }
                    }
                }
            }
        }
    )


def _temporada(anio, numero, ganadas, perdidas, abandonos=0) -> dict:
    return {
        "seasonYear": anio,
        "seasonNumber": numero,
        "matchesPlayed": ganadas + perdidas + abandonos,
        "matchesWon": ganadas,
        "matchesLost": perdidas,
        "roundsPlayed": 8 * (ganadas + perdidas),
        "roundsWon": 4 * (ganadas + perdidas),
        "kills": 300,
        "death": 250,
        "headshots": 120,
    }


def _temporadas(*filas) -> tuple[int, dict]:
    filas = filas or (
        _temporada("Y9", "S4", 40, 40),
        _temporada("Y10", "S2", 30, 20, abandonos=2),
        _temporada("Y10", "S1", 0, 0),
    )
    return 200, {
        "profileData": {
            PID.lower(): {
                "platforms": {"PC": {"gameModes": {"ranked": {"teamRoles": {"all": list(filas)}}}}}
            }
        }
    }


def _ubisoft_sano(**extra) -> FalsoUbisoft:
    rutas = {
        "profiles/sessions": [_login()],
        "full_profiles": [_perfiles()],
        "rewards/public_profile": [(200, {"level": 212, "xp": 1000})],
        "profiles/stats": [
            (200, {"profiles": [{"stats": {"PTotalTimePlayed": {"value": "1800000"}}}]})
        ],
        "aggregation=operators": [_operadores()],
        "aggregation=maps": [_mapas()],
        "aggregation=weapons": [_armas()],
        "view=seasonal": [_temporadas()],
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


class EstadisticasClienteTests(SimpleTestCase):
    """Operadores y mapas: lo que stats.cc muestra en esas pestanas."""

    def setUp(self):
        self.sesion = ubisoft.Sesion("tk-1", "ses-1", _expiracion())

    def estadisticas(self, **rutas):
        return ubisoft.perfil(self.sesion, PID, abrir=_ubisoft_sano(**rutas))["estadisticas"]

    def test_operadores_con_su_lado_y_numeros_desde_los_conteos(self):
        ranked = self.estadisticas()["operadores"]["ranked"]
        ash = next(f for f in ranked if f["operador"] == "Ash")
        self.assertEqual(ash["lado"], "Attack")
        self.assertEqual(ash["rondas"], 120)
        self.assertEqual(ash["partidas"], 10)
        self.assertEqual(ash["winrate"], 55.0)
        # el 9.99 que manda Ubisoft no se usa: bajas / muertes
        self.assertEqual(ash["kd"], 1.2)
        self.assertEqual(ash["kpr"], 0.8)
        self.assertEqual(ash["hs_pct"], 50.0)
        jager = next(f for f in ranked if f["operador"] == "Jäger")
        self.assertEqual(jager["lado"], "Defense")

    def test_la_fila_all_de_operadores_no_es_un_operador(self):
        """La fila `all` agrega los dos lados; contarla duplicaria a Ash."""
        ranked = self.estadisticas()["operadores"]["ranked"]
        self.assertEqual(sorted(f["operador"] for f in ranked), ["Ash", "Jäger"])

    def test_sin_rondas_no_hay_fila_ni_playlist(self):
        operadores = self.estadisticas()["operadores"]
        self.assertNotIn("IQ", [f["operador"] for f in operadores["ranked"]])
        self.assertNotIn("casual", operadores)

    def test_mapas_con_el_winrate_de_cada_lado(self):
        mapas = self.estadisticas()["mapas"]["ranked"]
        club = next(f for f in mapas if f["mapa"] == "Clubhouse")
        self.assertEqual(club["partidas"], 12)
        self.assertEqual(club["rondas"], 90)
        self.assertEqual(club["winrate"], 44.4)
        self.assertEqual(club["winrate_attack"], 33.3)
        self.assertEqual(club["winrate_defense"], 55.6)

    def test_un_mapa_sin_lados_o_sin_muertes_no_inventa(self):
        kafe = next(
            f for f in self.estadisticas()["mapas"]["ranked"] if f["mapa"] == "Kafe Dostoyevsky"
        )
        self.assertIsNone(kafe["winrate_attack"])
        self.assertIsNone(kafe["winrate_defense"])
        self.assertIsNone(kafe["kd"])
        # con bajas y ningun headshot es un 0 real, no un vacio
        self.assertEqual(kafe["hs_pct"], 0.0)

    def test_el_periodo_es_el_que_dice_ubisoft(self):
        datos = self.estadisticas()
        self.assertEqual(datos["desde"], "2026-06-01")
        self.assertEqual(datos["hasta"], "2026-09-30")

    def test_un_periodo_raro_no_se_adivina(self):
        raro = _playerstats({}, startDate="1 de junio", endDate="20260930")
        # el de operadores no sirve: se usa entero el de mapas, no medio de cada uno
        datos = self.estadisticas(**{"aggregation=operators": [raro]})
        self.assertEqual((datos["desde"], datos["hasta"]), ("2026-06-01", "2026-09-30"))

        sin_fecha = _playerstats({}, startDate=None, endDate=None)
        datos = self.estadisticas(
            **{
                "aggregation=operators": [raro],
                "aggregation=maps": [sin_fecha],
                "aggregation=weapons": [sin_fecha],
            }
        )
        self.assertEqual((datos["desde"], datos["hasta"]), (None, None))

    def test_pide_playerstats_de_pc_con_el_ticket(self):
        falso = _ubisoft_sano()
        ubisoft.perfil(self.sesion, PID, abrir=falso)
        pedidos = [p for p in falso.pedidos if "playerstats" in p.full_url]
        self.assertEqual(len(pedidos), 4)
        for pedido in pedidos:
            self.assertTrue(pedido.full_url.startswith("https://prod.datadev.ubisoft.com/"))
            self.assertIn("platformGroup=PC", pedido.full_url)
            self.assertIn(f"spaceId={ubisoft.ESPACIO}", pedido.full_url)
            self.assertEqual(pedido.get_header("Authorization"), "Ubi_v1 t=tk-1")
        # el periodo cuelga de /profiles/ y el historial de /users/, como en siegeapi
        rutas = sorted(p.full_url.split("/playerstats")[0].split("/v1/")[1] for p in pedidos)
        self.assertEqual(
            rutas, [f"profiles/{PID.lower()}"] * 3 + [f"users/{PID.lower()}"]
        )

    def test_acepta_la_respuesta_anidada_en_profile_data(self):
        """La forma del endpoint de resumenes; si Ubisoft unifica, no se rompe."""
        _, plano = _operadores()
        anidado = {"profileData": {PID.lower(): {"platforms": plano["platforms"]}}}
        datos = self.estadisticas(**{"aggregation=operators": [(200, anidado)]})
        self.assertEqual(len(datos["operadores"]["ranked"]), 2)

    def test_una_forma_desconocida_da_tablas_vacias_y_no_numeros(self):
        datos = self.estadisticas(
            **{
                "aggregation=operators": [(200, {"platforms": {"PC": {"gameModes": [1, 2]}}})],
                "aggregation=maps": [(200, {"algo": "nuevo"})],
            }
        )
        self.assertEqual(datos["operadores"], {})
        self.assertEqual(datos["mapas"], {})

    def test_si_playerstats_falla_el_rango_llega_igual_con_el_motivo(self):
        falso = _ubisoft_sano(**{"aggregation=maps": [(404, {"httpCode": 404})]})
        datos = ubisoft.perfil(self.sesion, PID, abrir=falso)
        self.assertEqual(datos["tableros"]["ranked"]["rango"], "Oro 1")
        self.assertIn("operadores, mapas y armas", datos["estadisticas"]["error"])
        self.assertNotIn("operadores", {k for k in datos["estadisticas"] if k != "error"})
        # el historial es otra ruta y llega igual
        self.assertIn("ranked", datos["historial"]["temporadas"])

    def test_un_401_en_playerstats_no_se_toma_como_ticket_vencido(self):
        """`full_profiles` acaba de aceptar el ticket: loguear de nuevo no lo arregla."""
        falso = _ubisoft_sano(**{"aggregation=operators": [(401, {"httpCode": 401})]})
        datos = ubisoft.perfil(self.sesion, PID, abrir=falso)
        self.assertIn("401", datos["estadisticas"]["error"])


class ArmasClienteTests(SimpleTestCase):
    def setUp(self):
        self.sesion = ubisoft.Sesion("tk-1", "ses-1", _expiracion())

    def armas(self, **rutas):
        datos = ubisoft.perfil(self.sesion, PID, abrir=_ubisoft_sano(**rutas))
        return datos["estadisticas"]["armas"]

    def test_recorre_todos_los_tipos_de_cada_ranura(self):
        ranked = self.armas()["ranked"]
        self.assertEqual([f["arma"] for f in ranked], ["R4-C", "MP5", "5.7 USG"])
        self.assertEqual([f["ranura"] for f in ranked], ["Principal", "Principal", "Secundaria"])
        self.assertEqual(ranked[1]["tipo"], "Submachine Gun")

    def test_numeros_de_un_arma(self):
        r4c = self.armas()["ranked"][0]
        self.assertEqual(r4c["rondas"], 120)
        self.assertEqual(r4c["winrate"], 55.0)
        self.assertEqual(r4c["bajas"], 90)
        self.assertEqual(r4c["kpr"], 0.75)
        self.assertEqual(r4c["hs_pct"], 50.0)
        # un arma no muere: no hay K/D que mostrar
        self.assertNotIn("kd", r4c)

    def test_sin_bajas_no_hay_hs_y_sin_rondas_no_hay_fila(self):
        ranked = self.armas()["ranked"]
        pistola = next(f for f in ranked if f["arma"] == "5.7 USG")
        self.assertIsNone(pistola["hs_pct"])
        self.assertNotIn("P9", [f["arma"] for f in ranked])

    def test_una_forma_desconocida_no_inventa_armas(self):
        raro = _playerstats({"ranked": {"teamRoles": {"all": [{"weaponName": "R4-C"}]}}})
        self.assertEqual(self.armas(**{"aggregation=weapons": [raro]}), {})


class HistorialClienteTests(SimpleTestCase):
    def setUp(self):
        self.sesion = ubisoft.Sesion("tk-1", "ses-1", _expiracion())

    def historial(self, **rutas):
        return ubisoft.perfil(self.sesion, PID, abrir=_ubisoft_sano(**rutas))["historial"]

    def test_una_fila_por_temporada_la_mas_nueva_primero(self):
        """Alfabeticamente Y9S4 iria antes que Y10S2."""
        ranked = self.historial()["temporadas"]["ranked"]
        self.assertEqual([f["temporada"] for f in ranked], ["Y10S2", "Y9S4"])

    def test_numeros_de_una_temporada(self):
        y10s2 = self.historial()["temporadas"]["ranked"][0]
        self.assertEqual(y10s2["partidas"], 52)
        self.assertEqual(y10s2["partidas_ganadas"], 30)
        # los abandonos cuentan como partida pero no entran al porcentaje
        self.assertEqual(y10s2["winrate_partidas"], 60.0)
        self.assertEqual(y10s2["winrate"], 50.0)
        self.assertEqual(y10s2["kd"], 1.2)

    def test_una_temporada_sin_partidas_no_es_una_fila(self):
        ranked = self.historial()["temporadas"]["ranked"]
        self.assertNotIn("Y10S1", [f["temporada"] for f in ranked])

    def test_acepta_el_codigo_con_numeros_sueltos_y_descarta_lo_raro(self):
        respuesta = _temporadas(
            _temporada(10, 3, 5, 5), _temporada("Y10", "Mid", 5, 5), _temporada("", "", 5, 5)
        )
        ranked = self.historial(**{"view=seasonal": [respuesta]})["temporadas"]["ranked"]
        self.assertEqual([f["temporada"] for f in ranked], ["Y10S3"])

    def test_si_falla_el_historial_los_operadores_llegan_igual(self):
        falso = _ubisoft_sano(**{"view=seasonal": [(404, {"httpCode": 404})]})
        datos = ubisoft.perfil(self.sesion, PID, abrir=falso)
        self.assertIn("historial por temporada", datos["historial"]["error"])
        self.assertIn("ranked", datos["estadisticas"]["operadores"])

    def test_orden_de_temporadas(self):
        self.assertGreater(ubisoft.orden_temporada("Y10S1"), ubisoft.orden_temporada("Y9S4"))


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

    def test_la_consulta_guarda_operadores_y_mapas(self):
        with self.con(_ubisoft_sano()):
            self.consultar()

        def prohibido(request):
            raise AssertionError("abrir un perfil no puede consultar a Ubisoft")

        with self.con(prohibido):
            data = self.client.get(f"/api/players/{self.amigo.id}/").json()
        estadisticas = data["externo"]["ubisoft"]["datos"]["estadisticas"]
        self.assertEqual(estadisticas["desde"], "2026-06-01")
        self.assertEqual(len(estadisticas["operadores"]["ranked"]), 2)
        self.assertEqual(estadisticas["mapas"]["ranked"][0]["mapa"], "Clubhouse")
        self.assertEqual(len(estadisticas["armas"]["ranked"]), 3)
        historial = data["externo"]["ubisoft"]["datos"]["historial"]
        self.assertEqual(historial["temporadas"]["ranked"][0]["temporada"], "Y10S2")
        # y al lado, lo que el panel cruza con eso
        self.assertIn("their_operators", data)
        self.assertIn("their_maps", data)
        self.assertIn("their_seasons", data)

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

    def test_un_401_en_operadores_no_hace_otro_login(self):
        """Ubisoft corta la IP con pocos logins, y uno nuevo no arreglaria ese 401."""
        falso = _ubisoft_sano(**{"aggregation=operators": [(401, {"httpCode": 401})]})
        with self.con(falso):
            respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(falso.contar("profiles/sessions"), 1)
        self.assertIn("401", respuesta.json()["datos"]["estadisticas"]["error"])
        self.assertEqual(respuesta.json()["datos"]["tableros"]["ranked"]["rango"], "Oro 1")

    def test_ticket_de_otra_cuenta_no_se_usa(self):
        self.guardar("ajeno", cuenta="otra@example.com")
        falso = _ubisoft_sano()
        with self.con(falso):
            self.consultar()
        self.assertEqual(falso.contar("profiles/sessions"), 1)
        self.assertNotIn("ajeno", json.dumps([p.headers for p in falso.pedidos]))
