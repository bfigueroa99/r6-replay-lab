"""Vigila la carpeta de replays e importa cada partida al terminar.

Usa polling en vez de watchdog: son unas pocas carpetas, no necesita
dependencias extra y no se confunde con los .rec a medio escribir.
"""

from __future__ import annotations

import signal
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from replays.ingest import find_match_folders, folder_is_settled, import_match_folder
from replays.models import Match


class Command(BaseCommand):
    help = "Importa automaticamente cada partida nueva que aparezca en REPLAY_DIR."

    def add_arguments(self, parser) -> None:
        parser.add_argument("path", nargs="?", help="Carpeta a vigilar (default: REPLAY_DIR).")
        parser.add_argument(
            "--interval", type=int, default=None, help="Segundos entre revisiones."
        )
        parser.add_argument(
            "--once", action="store_true", help="Una sola pasada y termina (util para tareas)."
        )

    def handle(self, *args, **options) -> None:
        root = Path(options["path"] or settings.REPLAY_DIR)
        if not root.exists():
            raise CommandError(f"No existe la carpeta {root}. Revisa REPLAY_DIR en el .env.")
        interval = options["interval"] or settings.WATCH_INTERVAL_SECONDS

        self.running = True

        def stop(*_):
            self.running = False
            self.stdout.write("\nCerrando el watcher...")

        signal.signal(signal.SIGINT, stop)
        try:
            signal.signal(signal.SIGTERM, stop)
        except (AttributeError, ValueError):  # Windows en algunos contextos
            pass

        self.stdout.write(
            self.style.SUCCESS(f"Vigilando {root} cada {interval}s. Ctrl+C para salir.")
        )
        pending_notice: set[str] = set()

        while self.running:
            known = set(Match.objects.values_list("folder", flat=True))
            for folder in find_match_folders(root):
                if folder.name in known:
                    continue
                if not folder_is_settled(folder, settings.IMPORT_QUIET_SECONDS):
                    if folder.name not in pending_notice:
                        pending_notice.add(folder.name)
                        self.stdout.write(f"  {folder.name}: partida en curso, esperando...")
                    continue
                pending_notice.discard(folder.name)
                self.stdout.write(f"  importando {folder.name}...")
                result = import_match_folder(folder)
                style = self.style.SUCCESS if result.ok else self.style.ERROR
                self.stdout.write(style(f"    {result.message} ({result.rounds} rondas)"))

            if options["once"]:
                break
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)
