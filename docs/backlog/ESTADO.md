# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-08 06:05 UTC por arquitecto (sesion 20261008T0602Z)
playbook: origin/claude/great-cray-7o9tvf@557a890
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| (vacia) | | | | |

COLA=0/3  TOTAL=0/5

## Orden de merge sugerido

Nada que mergear: no hay ramas de trabajo del equipo.

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|
| [30. Tests de quien gana la ronda y por que](30-tests-ganador-de-ronda.md) | disenado | 2 | parser | - |
| [31. Tests de stats por jugador: 1vX, headshots y agregado por partida](31-tests-stats-por-jugador.md) | disenado | 3 | parser | - |

Disenadas 30 y 31 sin archivos en comun (`tests/test_round_end.py` y `tests/test_player_stats.py`): se pueden implementar en paralelo. Papel: 0 propuesto, 2 disenado (tope del arquitecto alcanzado).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-08 00:01 | Crea la rama backlog y este tablero. Sin fichas que mergear. |
| arquitecto | 2026-10-08 06:02 | Disena 30 y 31 con los numeros corridos contra main dc0188b. Corrige dos criterios de la PO (el reloj del defuser agrega dos START; el 1v1 necesita otro escenario). Deja dos avisos en las fichas: bug de doble ganador en Y9S4 y 1vX que se pierde con un `PLAYER_LEAVE`. |
| po | 2026-10-08 03:02 | Propone 30 y 31 (tests de `round_end`, reloj del defuser, 1vX y stats por partida; criterios verificados contra main dc0188b). |

## Para el humano

- Ramas borrables (playbook anterior, solo commit de reclamo, sin codigo): `git push origin --delete claude/confident-feynman-dc9apf`
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador) y #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo en `## Para el equipo`.
  - **Bug en `round_end` (aviso de la ficha 30):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
