"""Exporta el JSON crudo de una ronda o partida, para depurar el parser."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pydissect import MatchReader, Reader, round_to_dict


class Command(BaseCommand):
    help = "Imprime (o guarda) el JSON que sale del parser para un .rec o una carpeta Match-*."

    def add_arguments(self, parser) -> None:
        parser.add_argument("path", help="Archivo .rec o carpeta Match-*")
        parser.add_argument("-o", "--output", help="Archivo de salida (default: stdout)")

    def handle(self, *args, **options) -> None:
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"No existe {path}")

        if path.is_dir():
            data = MatchReader(path).read().to_dict()
        else:
            reader = Reader.from_path(path)
            reader.read()
            data = round_to_dict(reader, path)

        text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        if options["output"]:
            Path(options["output"]).write_text(text, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"escrito en {options['output']}"))
        else:
            self.stdout.write(text)
