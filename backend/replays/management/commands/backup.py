"""Copia de seguridad de la base, con fecha y rotacion.

    manage.py backup              # deja data/backups/db-20260910-231500.sqlite3
    manage.py backup --keep 3     # y se queda solo con las 3 mas nuevas
    manage.py backup --list       # que copias hay

Vale la pena hacerlo seguido: reimportar el historial no siempre es posible,
porque el juego va borrando los replays viejos de MatchReplay.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from replays.backup import KEEP_DEFAULT, backup_database, backups_dir, existing_backups


def _humano(bytes_: int) -> str:
    return f"{bytes_ / (1024 * 1024):.2f} MB"


class Command(BaseCommand):
    help = "Deja una copia de la base en data/backups/ y borra las mas viejas."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--keep",
            type=int,
            default=KEEP_DEFAULT,
            help=f"Cuantas copias conservar (por defecto {KEEP_DEFAULT}). 0 las deja todas.",
        )
        parser.add_argument("--out", default=None, help="Carpeta destino.")
        parser.add_argument(
            "--list", action="store_true", help="Solo lista las copias que ya hay."
        )

    def handle(self, *args, **options) -> None:
        carpeta = options["out"] or backups_dir()

        if options["list"]:
            self._listar(carpeta)
            return

        try:
            result = backup_database(dest_dir=carpeta, keep=options["keep"])
        except FileNotFoundError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Copia lista: {result.path} ({_humano(result.size)})")
        )
        for borrada in result.removed:
            self.stdout.write(f"  se borro la copia vieja {borrada.name}")
        self._listar(carpeta)

    def _listar(self, carpeta) -> None:
        copias = existing_backups(carpeta)
        if not copias:
            self.stdout.write("No hay copias todavia.")
            return
        self.stdout.write(f"\n{len(copias)} copias en {carpeta}:")
        for copia in copias:
            self.stdout.write(f"  {copia.name}  {_humano(copia.stat().st_size)}")
