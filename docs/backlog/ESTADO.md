# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-08 15:08 UTC por dev (sesion 20261008T1502Z)
playbook: origin/claude/great-cray-7o9tvf@557a890
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/30-tests-ganador-de-ronda | docs/backlog/30-tests-ganador-de-ronda.md | revisado | 3 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/30-tests-ganador-de-ronda?expand=1) |
| claude/equipo-dev/31-tests-stats-por-jugador | docs/backlog/31-tests-stats-por-jugador.md | revisado | 3 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/31-tests-stats-por-jugador?expand=1) |
| claude/equipo-dev/32-days-enorme-da-500 | docs/backlog/32-days-enorme-da-500.md | implementado | 0 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/32-days-enorme-da-500?expand=1) |

COLA=3/3  TOTAL=3/5 (cola llena: nadie abre ramas nuevas hasta que se mergee algo)

## Orden de merge sugerido

1. `claude/equipo-dev/30-tests-ganador-de-ronda`: no choca con main ni con la 31 (merge de prueba limpio). Libera `backend/tests/test_round_end.py`.
2. `claude/equipo-dev/31-tests-stats-por-jugador`: no choca con nada. Libera `backend/tests/test_player_stats.py`.
3. `claude/equipo-dev/32-days-enorme-da-500`: no choca con main, 30 ni 31 (merge de prueba limpio). Libera `backend/replays/views.py` y `backend/tests/test_api.py`.

Las dos estan `revisado` (revisor 20261008T1202Z): esperan QA de una sesion distinta a 20261008T0902Z y 20261008T1202Z. Merge de prueba 30+31 limpio. La 32 esta `implementado`: espera revision de una sesion distinta a 20261008T1502Z.

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|
| [30. Tests de quien gana la ronda y por que](30-tests-ganador-de-ronda.md) | en curso (rama 30, revisado) | 2 | parser | - |
| [31. Tests de stats por jugador: 1vX, headshots y agregado por partida](31-tests-stats-por-jugador.md) | en curso (rama 31, revisado) | 3 | parser | - |
| [32. Un ?days= enorme da 500 en nueve endpoints](32-days-enorme-da-500.md) | en curso (rama 32, implementado) | 2 | backend | - |

Disenadas 30 y 31 sin archivos en comun (`tests/test_round_end.py` y `tests/test_player_stats.py`): implementadas en paralelo por el dev 20261008T0902Z. Papel: 0 propuesto, 0 disenado.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-08 00:01 | Crea la rama backlog y este tablero. Sin fichas que mergear. |
| revisor | 2026-10-08 12:02 | Revisa 30 y 31 (revision ciega + mutaciones). Hallazgos de test confirmados y cubiertos con tests de borde que agrego el revisor: Y9S4 con ganador equipo 1 y `startingScore` distinto de cero (30); kill con un companero vivo que no cuenta para el 1vX (31). Las dos -> `revisado`. |
| dev | 2026-10-08 15:02 | Sin fichas tomables (30 y 31 en `revisado`, papel vacio): bug real encontrado probando parametros borde sobre `seed_demo`. `?days=1000000` daba 500 en 10 endpoints (`OverflowError` en `_filters`). Ficha 32 escrita, arreglada (1 linea + 3 tests) y dejada en `implementado`. |
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
