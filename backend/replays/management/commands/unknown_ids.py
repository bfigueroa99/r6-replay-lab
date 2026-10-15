"""Lista los IDs de mapa, operador, modo y tipo de partida que el parser no supo nombrar.

Cada temporada de Siege trae IDs nuevos. Este comando los saca de la base ya
importada para que puedas etiquetarlos en `data/overrides.json`. La pagina
Datos de la app hace lo mismo desde el navegador; los dos leen `unknowns.py`.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from replays import unknowns


class Command(BaseCommand):
    help = "Muestra mapas, operadores, modos y tipos de partida sin nombre y como etiquetarlos."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Agrega los IDs desconocidos a overrides.json con valor vacio.",
        )

    def handle(self, *args, **options) -> None:
        maps = unknowns.unknown_maps()
        operators = unknowns.unknown_operators()
        gamemodes = unknowns.unknown_gamemodes()
        match_types = unknowns.unknown_match_types()
        path = unknowns.overrides_path()

        if not (maps or operators or gamemodes or match_types):
            self.stdout.write(self.style.SUCCESS("Todo identificado, nada que etiquetar."))
            return

        if maps:
            self.stdout.write(self.style.WARNING("Mapas sin nombre:"))
            for row in maps:
                self.stdout.write(f"  {row['id']}  ({row['matches']} partidas)")
                for site in row["sites"]:
                    self.stdout.write(f"      sitio visto: {site}")
                self.stdout.write(
                    "      (los nombres de los sitios delatan el mapa; buscalos en la wiki)"
                )

        if operators:
            self.stdout.write(self.style.WARNING("Operadores sin nombre:"))
            for row in operators:
                lado = ", ".join(row["sides"]) or "lado desconocido"
                self.stdout.write(f"  {row['id']}  ({row['rounds']} rondas, {lado})")

        if gamemodes:
            self.stdout.write(self.style.WARNING("Modos sin nombre:"))
            for row in gamemodes:
                tipos = ", ".join(row["match_types"]) or "tipo desconocido"
                self.stdout.write(f"  {row['id']}  ({row['matches']} partidas, {tipos})")

        if match_types:
            self.stdout.write(self.style.WARNING("Tipos de partida sin nombre:"))
            for row in match_types:
                modos = ", ".join(row["gamemodes"]) or "modo desconocido"
                self.stdout.write(f"  {row['id']}  ({row['matches']} partidas, {modos})")

        if options["write"]:
            unknowns.add_placeholders(
                [row["id"] for row in maps],
                [row["id"] for row in operators],
                [row["id"] for row in gamemodes],
                [row["id"] for row in match_types],
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nEscribi las entradas vacias en {path}. Rellenalas y corre "
                    "`manage.py retag` para etiquetar lo ya importado."
                )
            )
        else:
            self.stdout.write(
                f"\nEtiquetalos en {path} (o corre este comando con --write) asi:\n"
                '  {"maps": {"436375283234": "Coastline"}, "operators": {},\n'
                '   "gamemodes": {}, "match_types": {}}\n'
                "Tambien se pueden etiquetar desde la pagina Datos de la app."
            )
