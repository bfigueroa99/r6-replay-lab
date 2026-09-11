"""Tests del descubrimiento de IDs sin nombre y del endpoint que los etiqueta."""

from __future__ import annotations

import json

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
        self.assertEqual(unknowns.read_overrides(), {"maps": {}, "operators": {}})


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
