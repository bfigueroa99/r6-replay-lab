"""Re-aplica data/overrides.json sobre las partidas ya importadas.

Flujo tipico despues de una temporada nueva:

    manage.py unknown_ids --write    # deja las entradas vacias en overrides.json
    # rellenas los nombres a mano
    manage.py retag                  # y el historial queda etiquetado

Sin esto la unica salida era `import_replays --force`, que reparsea todos los
`.rec` para cambiar un nombre.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from replays.retag import retag


class Command(BaseCommand):
    help = "Re-etiqueta mapas y operadores de lo ya importado, sin reparsear los replays."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que cambiaria sin tocar la base.",
        )

    def handle(self, *args, **options) -> None:
        dry_run = options["dry_run"]
        result = retag(dry_run=dry_run)

        if not result.changed:
            self.stdout.write(
                self.style.SUCCESS("Nada que reetiquetar: los nombres ya estan al dia.")
            )
            return

        for change in result.changes:
            self.stdout.write(
                f"  {change.kind}: {change.old} -> {change.new} ({change.rows} filas)"
            )

        resumen = f"{result.matches} partidas y {result.round_players} rondas de jugador"
        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n[dry-run] cambiaria {resumen}."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nReetiquetadas {resumen}."))
