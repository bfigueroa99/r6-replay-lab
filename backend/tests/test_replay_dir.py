"""Autodeteccion de la carpeta MatchReplay (config/replay_dir.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from config import replay_dir

JUEGO = Path(replay_dir.NOMBRE_JUEGO) / replay_dir.MATCH_REPLAY


class BibliotecasSteamTests(SimpleTestCase):
    def test_lee_todas_las_rutas_del_vdf_y_desescapa_las_barras(self):
        with tempfile.TemporaryDirectory() as tmp:
            vdf = Path(tmp) / "libraryfolders.vdf"
            vdf.write_text(
                '"libraryfolders"\n{\n'
                '\t"0"\n\t{\n\t\t"path"\t\t"C:\\\\Program Files (x86)\\\\Steam"\n'
                '\t\t"label"\t\t""\n\t}\n'
                '\t"1"\n\t{\n\t\t"path"\t\t"D:\\\\SteamLibrary"\n\t}\n}\n',
                encoding="utf-8",
            )
            self.assertEqual(
                replay_dir.bibliotecas_steam(vdf),
                [Path(r"C:\Program Files (x86)\Steam"), Path(r"D:\SteamLibrary")],
            )

    def test_sin_archivo_devuelve_lista_vacia(self):
        self.assertEqual(replay_dir.bibliotecas_steam(Path("/no/existe.vdf")), [])


class CarpetaUbisoftTests(SimpleTestCase):
    def test_lee_la_carpeta_de_juegos_del_settings_yml(self):
        with tempfile.TemporaryDirectory() as tmp:
            yml = Path(tmp) / "settings.yml"
            yml.write_text(
                "misc:\n  game_installation_path: D:/Juegos/Ubisoft/games/\n"
                "user:\n  closebehavior: 0\n",
                encoding="utf-8",
            )
            self.assertEqual(
                replay_dir.carpeta_juegos_ubisoft(yml), Path("D:/Juegos/Ubisoft/games/")
            )

    def test_sin_la_clave_devuelve_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            yml = Path(tmp) / "settings.yml"
            yml.write_text("user:\n  closebehavior: 0\n", encoding="utf-8")
            self.assertIsNone(replay_dir.carpeta_juegos_ubisoft(yml))


class DeteccionTests(SimpleTestCase):
    def test_sin_launchers_ni_unidades_no_detecta_nada(self):
        self.assertIsNone(replay_dir.detectar(env={}, unidades=[]))

    def test_encuentra_el_juego_en_una_unidad_con_steam(self):
        with tempfile.TemporaryDirectory() as tmp:
            unidad = Path(tmp)
            carpeta = unidad / "Program Files (x86)/Steam/steamapps/common" / JUEGO
            carpeta.mkdir(parents=True)
            self.assertEqual(replay_dir.detectar(env={}, unidades=[unidad]), carpeta)

    def test_encuentra_el_juego_en_una_biblioteca_secundaria_de_steam(self):
        with tempfile.TemporaryDirectory() as tmp:
            pf = Path(tmp) / "pf86"
            biblioteca = Path(tmp) / "otra"
            (pf / "Steam" / "steamapps").mkdir(parents=True)
            (pf / "Steam" / "steamapps" / "libraryfolders.vdf").write_text(
                f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t"{biblioteca}"\n\t}}\n}}\n',
                encoding="utf-8",
            )
            carpeta = biblioteca / "steamapps/common" / JUEGO
            carpeta.mkdir(parents=True)
            env = {"ProgramFiles(x86)": str(pf)}
            self.assertEqual(replay_dir.detectar(env=env, unidades=[]), carpeta)

    def test_encuentra_el_juego_donde_dice_ubisoft_connect(self):
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local"
            juegos = Path(tmp) / "UbiGames"
            (local / "Ubisoft Game Launcher").mkdir(parents=True)
            (local / "Ubisoft Game Launcher" / "settings.yml").write_text(
                f"misc:\n  game_installation_path: {juegos}\n", encoding="utf-8"
            )
            carpeta = juegos / JUEGO
            carpeta.mkdir(parents=True)
            env = {"LOCALAPPDATA": str(local)}
            self.assertEqual(replay_dir.detectar(env=env, unidades=[]), carpeta)

    def test_el_launcher_gana_sobre_la_ruta_tipica(self):
        with tempfile.TemporaryDirectory() as tmp:
            unidad = Path(tmp)
            tipica = unidad / "Steam/steamapps/common" / JUEGO
            tipica.mkdir(parents=True)
            juegos = unidad / "Juegos"
            del_launcher = juegos / JUEGO
            del_launcher.mkdir(parents=True)
            local = unidad / "local"
            (local / "Ubisoft Game Launcher").mkdir(parents=True)
            (local / "Ubisoft Game Launcher" / "settings.yml").write_text(
                f"misc:\n  game_installation_path: {juegos}\n", encoding="utf-8"
            )
            env = {"LOCALAPPDATA": str(local)}
            self.assertEqual(replay_dir.detectar(env=env, unidades=[unidad]), del_launcher)

    def test_los_candidatos_no_se_repiten(self):
        with tempfile.TemporaryDirectory() as tmp:
            pf = Path(tmp) / "Program Files (x86)"
            pf.mkdir()
            env = {"ProgramFiles(x86)": str(pf)}
            rutas = replay_dir.candidatos(env=env, unidades=[Path(tmp)])
            self.assertEqual(len(rutas), len({str(r) for r in rutas}))
            # la misma carpeta de Steam llega por el env y por la unidad; una sola vez
            self.assertEqual(rutas[0], pf / "Steam/steamapps/common" / JUEGO)
