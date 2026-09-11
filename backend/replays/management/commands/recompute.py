"""Recalcula los trades de lo ya importado con la ventana configurada.

Los trades se guardan calculados al importar, asi que cambiar
`TRADE_WINDOW_SECONDS` en el `.env` no mueve nada hasta correr esto:

    manage.py recompute --dry-run    # cuanto cambiaria
    manage.py recompute

No abre ningun `.rec`: todo lo que hace falta esta en la base.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from replays.analytics.metrics import trade_window
from replays.recompute import recompute


class Command(BaseCommand):
    help = "Recalcula trades, muertes sin trade y KST con la ventana configurada."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--window",
            type=float,
            default=None,
            help="Ventana en segundos. Por defecto, la del .env.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que cambiaria sin tocar la base.",
        )

    def handle(self, *args, **options) -> None:
        window = options["window"] if options["window"] is not None else trade_window()
        if window <= 0:
            self.stderr.write(self.style.ERROR("La ventana tiene que ser mayor que cero."))
            return

        result = recompute(window=window, dry_run=options["dry_run"])
        resumen = (
            f"{result.players_changed} filas de jugador y {result.events_changed} eventos "
            f"sobre {result.rounds} rondas"
        )

        if not result.changed:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Nada que recalcular con ventana de {window:g}s: "
                    f"las {result.rounds} rondas ya estan al dia."
                )
            )
        elif options["dry_run"]:
            self.stdout.write(self.style.WARNING(f"[dry-run] con {window:g}s cambiarian {resumen}."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Con ventana de {window:g}s se actualizaron {resumen}."))
