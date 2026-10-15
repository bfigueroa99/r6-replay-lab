"""Tests del descubrimiento de IDs sin nombre y del endpoint que los etiqueta."""

from __future__ import annotations

import json
from datetime import datetime

from pydissect import overrides
from replays import unknowns
from replays.models import Match, RoundPlayer

from .factories import make_match, make_round, make_round_player
from .test_retag import MAPA_NUEVO, OPERADOR_NUEVO, OverridesTestCase


class DescubrimientoTests(OverridesTestCase):
    def setUp(self):
        super().setUp()
        self.match = make_match(map_name=f"Unknown({MAPA_NUEVO})", index=0, map_id=MAPA_NUEVO)
        for n, site in enumerate(["2F Dormitory, 2F Games Room", "1F Hammam, 1F Sitting Room"]):
            rnd = make_round(self.match, n, site=site)
            make_round_player(rnd, operator=f"Unknown({OPERADOR_NUEVO})", operator_id=OPERADOR_NUEVO)
        # una ronda mas en el mismo sitio: no puede duplicarse en la lista
        make_round_player(make_round(self.match, 2, site="2F Dormitory, 2F Games Room"))

    def test_mapa_desconocido_trae_las_pistas(self):
        row = unknowns.unknown_maps()[0]
        self.assertEqual(row["id"], str(MAPA_NUEVO))
        self.assertEqual(row["matches"], 1)
        self.assertEqual(row["rounds"], 3)
        self.assertEqual(
            row["sites"], ["1F Hammam, 1F Sitting Room", "2F Dormitory, 2F Games Room"]
        )

    def test_operador_desconocido_trae_el_lado(self):
        row = unknowns.unknown_operators()[0]
        self.assertEqual(row["id"], str(OPERADOR_NUEVO))
        self.assertEqual(row["rounds"], 2)
        self.assertEqual(row["sides"], ["Attack"])
        self.assertTrue(row["mine"])

    def test_lo_ya_identificado_no_aparece(self):
        make_match(map_name="Club House", index=1, map_id=837850796)
        self.assertEqual(len(unknowns.unknown_maps()), 1)

    def test_sin_id_crudo_no_se_puede_etiquetar(self):
        """Las partidas viejas sin map_id no salen: no hay nada que resolver."""
        Match.objects.filter(pk=self.match.pk).update(map_id=0)
        self.assertEqual(unknowns.unknown_maps(), [])


class ValidacionTests(OverridesTestCase):
    def test_acepta_ids_numericos(self):
        self.assertEqual(unknowns.clean_labels({"123": " Villa "}), {"123": "Villa"})

    def test_vacio_es_borrar(self):
        self.assertEqual(unknowns.clean_labels({"123": ""}), {"123": ""})
        self.assertEqual(unknowns.clean_labels(None), {})

    def test_rechaza_id_no_numerico(self):
        with self.assertRaises(unknowns.LabelError):
            unknowns.clean_labels({"no-soy-un-id": "Villa"})

    def test_rechaza_nombre_muy_largo(self):
        with self.assertRaises(unknowns.LabelError):
            unknowns.clean_labels({"123": "x" * 33})

    def test_rechaza_volver_a_poner_unknown(self):
        with self.assertRaises(unknowns.LabelError):
            unknowns.clean_labels({"123": "Unknown(123)"})

    def test_rechaza_lo_que_no_es_objeto(self):
        with self.assertRaises(unknowns.LabelError):
            unknowns.clean_labels(["Villa"])

    def test_placeholders_no_pisan_lo_que_ya_hay(self):
        unknowns.write_overrides({"1": "Villa"}, {})
        unknowns.add_placeholders(["1", "2"], [])
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["maps"], {"1": "Villa", "2": ""})

    def test_archivo_roto_no_revienta(self):
        self.path.write_text("{no es json", encoding="utf-8")
        self.assertEqual(
            unknowns.read_overrides(),
            {"maps": {}, "operators": {}, "gamemodes": {}, "match_types": {}},
        )


class EndpointTests(OverridesTestCase):
    def setUp(self):
        super().setUp()
        match = make_match(map_name=f"Unknown({MAPA_NUEVO})", index=0, map_id=MAPA_NUEVO)
        rnd = make_round(match, 0, site="2F Cigar Room, 2F Pool")
        make_round_player(rnd, operator=f"Unknown({OPERADOR_NUEVO})", operator_id=OPERADOR_NUEVO)

    def _post(self, payload):
        return self.client.post(
            "/api/overrides/", data=json.dumps(payload), content_type="application/json"
        )

    def test_get_lista_lo_desconocido(self):
        data = self.client.get("/api/unknown/").json()
        self.assertEqual(data["maps"][0]["id"], str(MAPA_NUEVO))
        self.assertEqual(data["maps"][0]["sites"], ["2F Cigar Room, 2F Pool"])
        self.assertEqual(data["operators"][0]["id"], str(OPERADOR_NUEVO))

    def test_guardar_etiqueta_y_reetiqueta(self):
        response = self._post({"maps": {str(MAPA_NUEVO): "Nighthaven Labs"}})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["matches"], 1)
        self.assertEqual(data["changes"][0]["new"], "Nighthaven Labs")
        match = Match.objects.get()
        self.assertEqual(match.map_name, "Nighthaven Labs")
        self.assertEqual(match.map_slug, "nighthaven-labs")
        # y deja de aparecer como desconocido
        self.assertEqual(self.client.get("/api/unknown/").json()["maps"], [])

    def test_guardar_operador(self):
        self._post({"operators": {str(OPERADOR_NUEVO): "Denari"}})
        self.assertEqual(RoundPlayer.objects.get().operator, "Denari")

    def test_el_archivo_queda_escrito(self):
        self._post({"maps": {str(MAPA_NUEVO): "Nighthaven Labs"}})
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["maps"][str(MAPA_NUEVO)], "Nighthaven Labs")

    def test_json_invalido_da_400(self):
        response = self.client.post(
            "/api/overrides/", data="{no es json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_id_invalido_da_400_y_no_escribe(self):
        response = self._post({"maps": {"drop table": "Villa"}})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.path.exists())

    def test_sin_etiquetas_da_400(self):
        self.assertEqual(self._post({}).status_code, 400)
        self.assertEqual(self._post({"maps": {}}).status_code, 400)

    def test_get_no_guarda(self):
        self.assertEqual(self.client.get("/api/overrides/").status_code, 405)


class ModosYTiposTests(OverridesTestCase):
    def _post(self, payload):
        return self.client.post(
            "/api/overrides/", data=json.dumps(payload), content_type="application/json"
        )

    def test_base_sin_desconocidos_da_listas_vacias(self):
        make_match(index=0)
        data = self.client.get("/api/unknown/").json()
        self.assertEqual((data["gamemodes"], data["match_types"]), ([], []))

    def test_modo_desconocido_lista_sus_partidas_y_fechas(self):
        make_match(gamemode="Unknown(999)", index=0, played_at=datetime(2026, 9, 1, 20, 0))
        make_match(gamemode="Unknown(999)", index=1, played_at=datetime(2026, 9, 5, 20, 0),
                   match_type="Unranked")
        make_match(gamemode="Bomb", index=2)
        filas = unknowns.unknown_gamemodes()
        self.assertEqual(len(filas), 1)
        fila = filas[0]
        self.assertEqual((fila["id"], fila["label"], fila["matches"]), ("999", "Unknown(999)", 2))
        self.assertTrue(fila["first_seen"].startswith("2026-09-01"))
        self.assertTrue(fila["last_seen"].startswith("2026-09-05"))
        self.assertEqual(fila["match_types"], ["Ranked", "Unranked"])
        self.assertEqual(fila["pending"], "")

    def test_tipo_desconocido_trae_los_modos_como_pista(self):
        make_match(match_type="Unknown(77)", gamemode="Hostage", index=0)
        fila = unknowns.unknown_match_types()[0]
        self.assertEqual((fila["id"], fila["gamemodes"]), ("77", ["Hostage"]))

    def test_unknown_0_no_se_lista(self):
        make_match(gamemode="Unknown(0)", match_type="Unknown(0)", index=0)
        self.assertEqual(unknowns.unknown_gamemodes(), [])
        self.assertEqual(unknowns.unknown_match_types(), [])

    def test_etiqueta_pendiente_se_muestra(self):
        make_match(gamemode="Unknown(999)", index=0)
        self.path.write_text(json.dumps({"gamemodes": {"999": "Arcade"}}), encoding="utf-8")
        overrides.load(force=True)
        self.assertEqual(unknowns.unknown_gamemodes()[0]["pending"], "Arcade")

    def test_guardar_etiqueta_de_modo_y_reetiqueta(self):
        make_match(gamemode="Unknown(999)", index=0)
        response = self._post({"gamemodes": {"999": "Arcade"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["saved"]["gamemodes"], {"999": "Arcade"})
        self.assertEqual(Match.objects.get().gamemode, "Arcade")
        self.assertEqual(self.client.get("/api/unknown/").json()["gamemodes"], [])
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["gamemodes"], {"999": "Arcade"})

    def test_solo_etiquetas_de_tipo_alcanza_para_guardar(self):
        make_match(match_type="Unknown(77)", index=0)
        self.assertEqual(self._post({"match_types": {"77": "Evento"}}).status_code, 200)
        self.assertEqual(Match.objects.get().match_type, "Evento")

    def test_id_de_modo_no_numerico_da_400_y_no_escribe(self):
        response = self._post({"gamemodes": {"abc": "Arcade"}})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.path.exists())
        self.assertEqual(self._post({"match_types": "no"}).status_code, 400)

    def test_guardar_mapa_no_borra_las_etiquetas_de_modo(self):
        self.path.write_text(json.dumps({"gamemodes": {"999": "Arcade"}}), encoding="utf-8")
        self._post({"maps": {"1": "Villa"}})
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["gamemodes"], {"999": "Arcade"})
        self.assertEqual(data["maps"], {"1": "Villa"})

    def test_overrides_viejo_sin_claves_nuevas_se_lee(self):
        self.path.write_text(json.dumps({"maps": {"1": "Villa"}, "operators": {}}), encoding="utf-8")
        data = unknowns.read_overrides()
        self.assertEqual(data["gamemodes"], {})
        self.assertEqual(data["match_types"], {})
        self.assertEqual(data["maps"], {"1": "Villa"})

    def test_id_de_unknown(self):
        self.assertEqual(unknowns.id_de_unknown("Unknown(999)"), 999)
        self.assertIsNone(unknowns.id_de_unknown("Unknown(0)"))
        self.assertIsNone(unknowns.id_de_unknown("Unknown(abc)"))
        self.assertIsNone(unknowns.id_de_unknown("Bomb"))
        self.assertIsNone(unknowns.id_de_unknown(""))
