"""Lista los IDs de mapa/operador que el parser no supo nombrar.

Cada temporada de Siege trae IDs nuevos. Este comando los saca de la base de
datos ya importada para que puedas etiquetarlos en data/overrides.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from replays.models import Match, Round, RoundPlayer

UNKNOWN = re.compile(r"^Unknown\((\d+)\)$")


class Command(BaseCommand):
    help = "Muestra mapas y operadores sin nombre y como etiquetarlos."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Agrega los IDs desconocidos a data/overrides.json con valor vacio.",
        )

    def handle(self, *args, **options) -> None:
        maps = {}
        for match in Match.objects.filter(map_name__startswith="Unknown("):
            m = UNKNOWN.match(match.map_name)
            if m:
                sites = list(
                    Round.objects.filter(match=match)
                    .exclude(site="")
                    .values_list("site", flat=True)
                    .distinct()
                )
                maps[int(m.group(1))] = sites

        operators = set()
        for name in (
            RoundPlayer.objects.filter(operator__startswith="Unknown(")
            .values_list("operator", flat=True)
            .distinct()
        ):
            m = UNKNOWN.match(name)
            if m:
                operators.add(int(m.group(1)))

        if not maps and not operators:
            self.stdout.write(self.style.SUCCESS("Todo identificado, nada que etiquetar."))
            return

        if maps:
            self.stdout.write(self.style.WARNING("Mapas sin nombre:"))
            for map_id, sites in maps.items():
                self.stdout.write(f"  {map_id}")
                for site in sites:
                    self.stdout.write(f"      sitio visto: {site}")
                self.stdout.write(
                    "      (los nombres de los sitios delatan el mapa; buscalos en la wiki)"
                )
        if operators:
            self.stdout.write(self.style.WARNING("Operadores sin nombre:"))
            for op_id in sorted(operators):
                self.stdout.write(f"  {op_id}")

        path = Path(settings.DATA_DIR) / "overrides.json"
        if options["write"]:
            data = {"maps": {}, "operators": {}}
            if path.exists():
                data.update(json.loads(path.read_text(encoding="utf-8")))
            data.setdefault("maps", {})
            data.setdefault("operators", {})
            for map_id in maps:
                data["maps"].setdefault(str(map_id), "")
            for op_id in operators:
                data["operators"].setdefault(str(op_id), "")
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nEscribi las entradas vacias en {path}. Rellenalas y corre "
                    "`manage.py import_replays --force` para reetiquetar."
                )
            )
        else:
            self.stdout.write(
                f"\nEtiquetalos en {path} (o corre este comando con --write) asi:\n"
                '  {"maps": {"436375283234": "Coastline"}, "operators": {}}'
            )
