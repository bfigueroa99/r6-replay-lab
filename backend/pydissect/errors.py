"""Errores del parser Dissect."""


class DissectError(Exception):
    """Base de todos los errores del parser."""


class InvalidFile(DissectError):
    """El archivo no tiene la firma `dissect` ni un frame zstd al inicio."""


class InvalidStringSep(DissectError):
    """Se esperaba el separador de 7 bytes nulos y no estaba."""


class InvalidFolder(DissectError):
    """La carpeta no contiene archivos .rec."""


class EndOfFile(DissectError):
    """Se llego al final del buffer (equivalente a io.EOF)."""
