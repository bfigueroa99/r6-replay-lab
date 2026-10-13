"""Ajustes desde la app: el .env editable, la carpeta, las copias y el vigilante."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, TestCase

from config import envfile, replay_dir
from replays import backup, ingest, vigilante
from replays.models import ImportLog, Match

from .factories import make_match


def _tmp(test) -> Path:
    carpeta = Path(tempfile.mkdtemp())
    test.addCleanup(shutil.rmtree, carpeta, True)
    return carpeta


def _partida(raiz: Path, nombre: str, *, hace: float = 3600) -> Path:
    """Una carpeta Match-* con un .rec falso, escrita hace `hace` segundos."""
    carpeta = raiz / nombre
    carpeta.mkdir(parents=True)
    rec = carpeta / "r.rec"
    rec.write_bytes(b"no soy un replay")
    viejo = time.time() - hace
    os.utime(rec, (viejo, viejo))
    return carpeta


class EnvFileTests(SimpleTestCase):
    def setUp(self):
        self.env = _tmp(self) / ".env"

    def test_sin_archivo_lee_vacio(self):
        self.assertEqual(envfile.leer(self.env), {})

    def test_lee_como_settings_gana_la_primera_y_sin_comillas(self):
        self.env.write_text('# comentario\nA=1\nB="dos"\nA=3\n', encoding="utf-8")
        self.assertEqual(envfile.leer(self.env), {"A": "1", "B": "dos"})

    def test_cambiar_una_clave_respeta_comentarios_y_el_resto(self):
        self.env.write_text(
            "# carpeta de Siege\nREPLAY_DIR=C:\\viejo\nTRADE_WINDOW_SECONDS=3\n", encoding="utf-8"
        )
        envfile.escribir(self.env, {"REPLAY_DIR": r"D:\Juegos\MatchReplay"})
        self.assertEqual(
            self.env.read_text(encoding="utf-8"),
            "# carpeta de Siege\nREPLAY_DIR=D:\\Juegos\\MatchReplay\nTRADE_WINDOW_SECONDS=3\n",
        )

    def test_una_clave_nueva_va_al_final(self):
        self.env.write_text("A=1\n", encoding="utf-8")
        envfile.escribir(self.env, {"AUTO_IMPORT": "false"})
        self.assertEqual(self.env.read_text(encoding="utf-8"), "A=1\n\nAUTO_IMPORT=false\n")

    def test_crea_el_archivo_y_la_carpeta_si_no_existen(self):
        destino = self.env.parent / "sub" / ".env"
        envfile.escribir(destino, {"A": "1"})
        self.assertEqual(envfile.leer(destino), {"A": "1"})

    def test_none_borra_la_clave_y_sus_duplicados(self):
        self.env.write_text("REPLAY_DIR=x\nA=1\nREPLAY_DIR=y\n", encoding="utf-8")
        envfile.escribir(self.env, {"REPLAY_DIR": None})
        self.assertEqual(envfile.leer(self.env), {"A": "1"})

    def test_un_comentario_con_la_clave_no_se_toca(self):
        self.env.write_text("# REPLAY_DIR=D:\\ejemplo\n", encoding="utf-8")
        envfile.escribir(self.env, {"REPLAY_DIR": "E:\\otra"})
        texto = self.env.read_text(encoding="utf-8")
        self.assertIn("# REPLAY_DIR=D:\\ejemplo", texto)
        self.assertEqual(envfile.leer(self.env), {"REPLAY_DIR": "E:\\otra"})

    def test_un_salto_de_linea_no_cuela_otra_clave(self):
        self.env.write_text("A=1\n", encoding="utf-8")
        with self.assertRaises(envfile.ValorInvalido):
            envfile.escribir(self.env, {"REPLAY_DIR": "C:\\x\nDJANGO_DEBUG=true"})
        # y no escribio nada a medias
        self.assertEqual(self.env.read_text(encoding="utf-8"), "A=1\n")

    def test_una_clave_rara_se_rechaza(self):
        with self.assertRaises(envfile.ValorInvalido):
            envfile.escribir(self.env, {"a b": "1"})


class ResolverCarpetaTests(SimpleTestCase):
    def test_lo_elegido_gana_aunque_no_exista(self):
        self.assertEqual(replay_dir.resolver("D:\\no\\existe"), ("D:\\no\\existe", "elegida"))

    def test_sin_eleccion_busca_sola(self):
        with mock.patch.object(replay_dir, "detectar", return_value=Path("/juegos/MatchReplay")):
            self.assertEqual(replay_dir.resolver(""), (str(Path("/juegos/MatchReplay")), "detectada"))

    def test_sin_nada_cae_en_la_ruta_por_defecto(self):
        with mock.patch.object(replay_dir, "detectar", return_value=None):
            ruta, origen = replay_dir.resolver(None)
        self.assertEqual(origen, "no_encontrada")
        self.assertEqual(ruta, str(replay_dir.POR_DEFECTO))


class NormalizarCarpetaTests(SimpleTestCase):
    def setUp(self):
        self.raiz = _tmp(self)

    def test_la_carpeta_del_juego_baja_a_su_match_replay(self):
        juego = self.raiz / replay_dir.NOMBRE_JUEGO
        (juego / "MatchReplay").mkdir(parents=True)
        self.assertEqual(replay_dir.normalizar(juego), juego / "MatchReplay")

    def test_la_biblioteca_baja_dos_niveles(self):
        destino = self.raiz / replay_dir.NOMBRE_JUEGO / "MatchReplay"
        destino.mkdir(parents=True)
        self.assertEqual(replay_dir.normalizar(self.raiz), destino)

    def test_una_carpeta_con_partidas_se_queda_como_esta(self):
        (self.raiz / "Match-2026-01-01").mkdir()
        (self.raiz / "MatchReplay").mkdir()
        self.assertEqual(replay_dir.normalizar(self.raiz), self.raiz)

    def test_sin_nada_abajo_se_queda_como_esta(self):
        self.assertEqual(replay_dir.normalizar(self.raiz), self.raiz)


class AjustesApiTests(TestCase):
    def setUp(self):
        self.tmp = _tmp(self)
        self.env = self.tmp / ".env"
        self.datos = self.tmp / "data"
        ctx = self.settings(
            ENV_FILE=self.env,
            DATA_DIR=self.datos,
            REPLAY_DIR=str(self.tmp / "no-existe"),
            REPLAY_DIR_ORIGEN="no_encontrada",
            AUTO_IMPORT=True,
        )
        ctx.enable()
        self.addCleanup(ctx.disable)

    def _post(self, body, content_type="application/json"):
        return self.client.post("/api/settings/", data=json.dumps(body), content_type=content_type)

    def test_get_trae_carpeta_vigilante_y_copias(self):
        data = self.client.get("/api/settings/").json()
        self.assertEqual(data["replay_dir_source"], "no_encontrada")
        self.assertFalse(data["replay_dir_exists"])
        self.assertEqual(data["replay_dir_folders"], 0)
        self.assertTrue(data["auto_import"]["enabled"])
        self.assertIn("running", data["auto_import"])
        self.assertEqual(data["backups"]["items"], [])
        self.assertEqual(data["env_file"], str(self.env))

    def test_elegir_una_carpeta_la_guarda_y_la_aplica_sin_reiniciar(self):
        carpeta = self.tmp / "MatchReplay"
        _partida(carpeta, "Match-a")

        data = self._post({"replay_dir": str(carpeta)}).json()
        self.assertEqual(data["replay_dir"], str(carpeta))
        self.assertEqual(data["replay_dir_source"], "elegida")
        self.assertTrue(data["replay_dir_exists"])
        self.assertEqual(data["replay_dir_folders"], 1)
        self.assertEqual(envfile.leer(self.env), {"REPLAY_DIR": str(carpeta)})
        # el resto de la app ya usa la nueva, sin reiniciar
        self.assertEqual(self.client.get("/api/import/status/").json()["folders_on_disk"], 1)

    def test_elegir_la_carpeta_del_juego_guarda_su_match_replay(self):
        juego = self.tmp / replay_dir.NOMBRE_JUEGO
        (juego / "MatchReplay").mkdir(parents=True)
        data = self._post({"replay_dir": str(juego)}).json()
        self.assertEqual(data["replay_dir"], str(juego / "MatchReplay"))

    def test_una_carpeta_que_no_existe_no_se_guarda(self):
        respuesta = self._post({"replay_dir": str(self.tmp / "inventada")})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("No existe la carpeta", respuesta.json()["error"])
        self.assertFalse(self.env.exists())

    def test_una_ruta_relativa_no_se_guarda(self):
        respuesta = self._post({"replay_dir": "MatchReplay"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("ruta completa", respuesta.json()["error"])

    def test_vaciarla_vuelve_a_buscarla_sola(self):
        self.env.write_text("REPLAY_DIR=C:\\vieja\nA=1\n", encoding="utf-8")
        with mock.patch.object(replay_dir, "detectar", return_value=None):
            data = self._post({"replay_dir": ""}).json()
        self.assertEqual(data["replay_dir_source"], "no_encontrada")
        self.assertEqual(envfile.leer(self.env), {"A": "1"})

    def test_apagar_la_importacion_automatica(self):
        data = self._post({"auto_import": False}).json()
        self.assertFalse(data["auto_import"]["enabled"])
        self.assertEqual(envfile.leer(self.env), {"AUTO_IMPORT": "false"})

    def test_auto_import_tiene_que_ser_booleano(self):
        respuesta = self._post({"auto_import": "no"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.env.exists())

    def test_si_una_parte_falla_no_se_guarda_ninguna(self):
        respuesta = self._post({"auto_import": False, "replay_dir": str(self.tmp / "inventada")})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.env.exists())

    def test_sin_ajustes_es_400(self):
        self.assertEqual(self._post({}).status_code, 400)

    def test_un_formulario_de_otra_pagina_no_cambia_nada(self):
        """`text/plain` es lo que puede mandar un <form> ajeno sin preflight."""
        respuesta = self._post({"auto_import": False}, content_type="text/plain")
        self.assertEqual(respuesta.status_code, 415)
        self.assertFalse(self.env.exists())

    def test_json_roto_es_400(self):
        respuesta = self.client.post(
            "/api/settings/", data="{no", content_type="application/json"
        )
        self.assertEqual(respuesta.status_code, 400)


class BackupApiTests(TestCase):
    def setUp(self):
        self.tmp = _tmp(self)
        self.base = self.tmp / "db.sqlite3"
        con = sqlite3.connect(self.base)
        con.execute("CREATE TABLE t (x)")
        con.commit()
        con.close()
        ctx = self.settings(DATA_DIR=self.tmp)
        ctx.enable()
        self.addCleanup(ctx.disable)
        # la base de los tests vive en memoria: se apunta la copia a una de verdad
        parche = mock.patch.object(backup, "database_path", return_value=self.base)
        parche.start()
        self.addCleanup(parche.stop)

    def _post(self, content_type="application/json"):
        return self.client.post("/api/backup/", data="{}", content_type=content_type)

    def test_hace_la_copia_y_la_lista(self):
        data = self._post().json()
        self.assertTrue(data["name"].startswith("db-"))
        self.assertTrue((self.tmp / "backups" / data["name"]).exists())
        self.assertEqual([c["name"] for c in data["backups"]["items"]], [data["name"]])
        self.assertEqual(data["removed"], [])

    def test_la_lista_sale_tambien_en_ajustes(self):
        nombre = self._post().json()["name"]
        items = self.client.get("/api/settings/").json()["backups"]["items"]
        self.assertEqual(items[0]["name"], nombre)
        self.assertGreater(items[0]["size"], 0)

    def test_sin_json_no_copia(self):
        """Diez POST de una pagina ajena rotarian las copias viejas."""
        self.assertEqual(self._post(content_type="text/plain").status_code, 415)
        self.assertFalse((self.tmp / "backups").exists())

    def test_sin_base_lo_dice(self):
        self.base.unlink()
        respuesta = self._post()
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("no existe la base", respuesta.json()["error"])

    def test_get_no_hace_copias(self):
        self.assertEqual(self.client.get("/api/backup/").status_code, 405)


class CopiaSemanalTests(TestCase):
    def setUp(self):
        self.tmp = _tmp(self)
        ctx = self.settings(DATA_DIR=self.tmp)
        ctx.enable()
        self.addCleanup(ctx.disable)

    def _copia(self, hace_dias: float) -> None:
        carpeta = self.tmp / "backups"
        carpeta.mkdir(exist_ok=True)
        copia = carpeta / f"db-{hace_dias}.sqlite3"
        copia.write_bytes(b"x")
        cuando = time.time() - hace_dias * 86400
        os.utime(copia, (cuando, cuando))

    def test_sin_copias_hace_falta(self):
        self.assertTrue(backup.hace_falta_copia())

    def test_con_una_de_ayer_no(self):
        self._copia(1)
        self.assertFalse(backup.hace_falta_copia())

    def test_con_una_de_hace_ocho_dias_si(self):
        self._copia(8)
        self.assertTrue(backup.hace_falta_copia())

    def test_manda_la_mas_nueva(self):
        self._copia(30)
        self._copia(2)
        self.assertFalse(backup.hace_falta_copia())

    def test_al_arrancar_sin_partidas_no_copia(self):
        import serve

        with mock.patch("replays.backup.backup_database") as copiar:
            serve.copia_semanal()
        copiar.assert_not_called()

    def test_al_arrancar_con_partidas_y_sin_copias_copia(self):
        import serve

        make_match(index=0)
        with mock.patch("replays.backup.backup_database") as copiar:
            serve.copia_semanal()
        copiar.assert_called_once()

    def test_si_la_copia_falla_la_app_abre_igual(self):
        import serve

        make_match(index=0)
        with mock.patch("replays.backup.backup_database", side_effect=OSError("disco lleno")):
            with self.assertLogs("serve", level="ERROR"):
                serve.copia_semanal()


class VigilanteTests(TestCase):
    """`revisar` es sincrona: en los tests un hilo no ve la transaccion."""

    def setUp(self):
        self.raiz = _tmp(self)
        ctx = self.settings(REPLAY_DIR=str(self.raiz), AUTO_IMPORT=True, IMPORT_QUIET_SECONDS=60)
        ctx.enable()
        self.addCleanup(ctx.disable)
        self.addCleanup(vigilante._intentadas.clear)
        self.addCleanup(setattr, ingest, "_job", ingest.ImportJob())
        vigilante._intentadas.clear()
        ingest._job = ingest.ImportJob()

    def test_importa_lo_que_ya_termino_y_lo_marca_como_automatico(self):
        _partida(self.raiz, "Match-a")
        self.assertEqual(vigilante.revisar(), 1)
        job = ingest.import_job().as_dict()
        self.assertEqual(job["origin"], "auto")
        self.assertFalse(job["running"])
        # el .rec es falso: falla al parsear, pero queda registrado
        self.assertEqual(job["errors"], 1)
        self.assertEqual(ImportLog.objects.filter(folder="Match-a").count(), 1)

    def test_no_toca_una_partida_que_se_esta_jugando(self):
        _partida(self.raiz, "Match-a", hace=5)
        self.assertEqual(vigilante.revisar(), 0)

    def test_apagada_no_hace_nada(self):
        _partida(self.raiz, "Match-a")
        with self.settings(AUTO_IMPORT=False):
            self.assertEqual(vigilante.revisar(), 0)
        self.assertFalse(ImportLog.objects.exists())

    def test_sin_carpeta_no_hace_nada(self):
        with self.settings(REPLAY_DIR=str(self.raiz / "no-existe")):
            self.assertEqual(vigilante.revisar(), 0)

    def test_una_carpeta_que_falla_no_se_reintenta_cada_pasada(self):
        _partida(self.raiz, "Match-a")
        vigilante.revisar()
        self.assertEqual(vigilante.revisar(), 0)
        self.assertEqual(vigilante.revisar(), 0)
        self.assertEqual(ImportLog.objects.filter(folder="Match-a").count(), 1)

    def test_si_la_carpeta_cambia_se_reintenta(self):
        carpeta = _partida(self.raiz, "Match-a", hace=7200)
        vigilante.revisar()
        rec = carpeta / "r2.rec"
        rec.write_bytes(b"otra ronda")
        viejo = time.time() - 3600
        os.utime(rec, (viejo, viejo))
        self.assertEqual(vigilante.revisar(), 1)

    def test_sin_nada_nuevo_no_pisa_el_resultado_de_la_ultima(self):
        """Revisa cada 20 s: un trabajo vacio borraria lo que muestra la UI."""
        ultimo = ingest.ImportJob(total=3, done=3, origin="manual")
        ingest._job = ultimo
        self.assertEqual(vigilante.revisar(), 0)
        self.assertIs(ingest.import_job(), ultimo)

    def test_no_se_mete_si_el_boton_ya_esta_importando(self):
        _partida(self.raiz, "Match-a")
        ingest._job = ingest.ImportJob(running=True, total=5)
        self.assertEqual(vigilante.revisar(), 0)
        self.assertFalse(ImportLog.objects.exists())

    def test_una_ya_importada_no_vuelve_a_entrar(self):
        _partida(self.raiz, "Match-a")
        match = make_match(index=0)
        Match.objects.filter(pk=match.pk).update(folder="Match-a")
        self.assertEqual(vigilante.revisar(), 0)

    def test_estado_dice_si_hay_hilo(self):
        with self.settings(WATCH_INTERVAL_SECONDS=20):
            estado = vigilante.estado()
        self.assertTrue(estado["enabled"])
        self.assertFalse(estado["running"])
        self.assertEqual(estado["interval"], 20)


class HiloVigilanteTests(SimpleTestCase):
    def test_arranca_una_sola_vez_y_se_detiene(self):
        with self.settings(AUTO_IMPORT=False, WATCH_INTERVAL_SECONDS=1):
            self.addCleanup(vigilante.detener)
            self.assertTrue(vigilante.iniciar())
            self.assertFalse(vigilante.iniciar())
            self.assertTrue(vigilante.corriendo())
            vigilante.detener()
            self.assertFalse(vigilante.corriendo())


class OrigenDelTrabajoTests(TestCase):
    def setUp(self):
        self.addCleanup(setattr, ingest, "_job", ingest.ImportJob())

    def test_el_boton_queda_como_manual(self):
        with self.settings(REPLAY_DIR="/ruta/que/no/existe"):
            data = self.client.post("/api/import/").json()
        self.assertEqual(data["origin"], "manual")
        for _ in range(50):
            if not ingest.import_job().running:
                break
            time.sleep(0.02)

    def test_reservar_sin_nada_y_sin_forzar_no_deja_trabajo(self):
        anterior = ingest.import_job()
        self.assertIsNone(ingest.reserve_import("/ruta/que/no/existe", even_if_empty=False))
        self.assertIs(ingest.import_job(), anterior)
