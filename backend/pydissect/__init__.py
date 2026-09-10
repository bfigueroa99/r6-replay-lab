"""pydissect — parser en Python puro del formato .rec de Rainbow Six Siege.

Port del reverse engineering de r6-dissect (redraskal, licencia MIT). No
necesita binarios externos ni la CLI de Go: solo `zstandard`.

Ejemplo::

    from pydissect import MatchReader, Reader

    r = Reader.from_path("Match-...-R01.rec")
    r.read()
    print(r.header["site"], r.match_feedback[:3])

    m = MatchReader("Match-2026-09-09_17-20-05-21072").read()
    data = m.to_dict()
"""

from .errors import DissectError, InvalidFile, InvalidFolder, InvalidStringSep
from .match import MatchReader, list_replay_files, round_to_dict
from .reader import Reader
from .stats import (
    kills_and_deaths,
    opening_death,
    opening_kill,
    player_match_stats,
    player_round_stats,
    trades,
)

__all__ = [
    "DissectError",
    "InvalidFile",
    "InvalidFolder",
    "InvalidStringSep",
    "MatchReader",
    "Reader",
    "kills_and_deaths",
    "list_replay_files",
    "opening_death",
    "opening_kill",
    "player_match_stats",
    "player_round_stats",
    "round_to_dict",
    "trades",
]

__version__ = "0.1.0"
