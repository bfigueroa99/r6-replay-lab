"""Importa replays desde la carpeta de Siege (o desde una ruta puntual)."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from replays.ingest import find_match_folders, import_match_folder, scan_and_import


class Command(BaseCommand):
    help = "Parsea los .rec y los guarda en la base de datos."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "path",
            nargs="?",
            help="Carpeta de replays o una carpeta Match-* puntual. "
            "Por defecto usa REPLAY_DIR del .env.",
        )
        parser.add_argument("--force", action="store_true", help="Reimporta lo ya importado.")
        parser.add_argument("--limit", type=int, default=0, help="Maximo de partidas a importar.")
        parser.add_argument(
            "--quiet-seconds",
            type=int,
            default=None,
            help="Segundos sin cambios para considerar terminada una partida (0 para ignorar).",
        )

    def handle(self, *args, **options) -> None:
        root = Path(options["path"] or settings.REPLAY_DIR)
        if not root.exists():
            raise CommandError(
                f"No existe la carpeta {root}. Revisa REPLAY_DIR en el .env."
            )

        quiet = options["quiet_seconds"]
        if quiet is None:
            quiet = settings.IMPORT_QUIET_SECONDS

        if any(root.glob("*.rec")):
            results = [import_match_folder(root, force=options["force"])]
        else:
            folders = find_match_folders(root)
            if not folders:
                raise CommandError(f"No encontre carpetas Match-* con .rec en {root}")
            self.stdout.write(f"{len(folders)} partidas en disco")
            results = scan_and_import(
                root,
                quiet_seconds=quiet,
                force=options["force"],
                limit=options["limit"] or None,
            )

        ok = [r for r in results if r.ok]
        bad = [r for r in results if not r.ok]
        for r in results:
            style = self.style.SUCCESS if r.ok else self.style.ERROR
            self.stdout.write(style(f"  {r.folder}: {r.message} ({r.rounds} rondas)"))
        if not results:
            self.stdout.write("Nada nuevo para importar.")
        self.stdout.write(
            self.style.SUCCESS(f"Listo: {len(ok)} importadas, {len(bad)} con error.")
        )
