# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-09 00:30 UTC por release (sesion 20261009T0002Z)
playbook: origin/claude/great-cray-7o9tvf@557a890
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/32-days-enorme-da-500 | docs/backlog/32-days-enorme-da-500.md | revisado | 3 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/32-days-enorme-da-500?expand=1) |

COLA=1/3  TOTAL=1/5 (hay lugar: el Dev puede tomar `disenado`, pero el papel esta vacio)

Mergeados a main este turno (puerta completa: dev, revisor y qa de tres sesiones; `check.sh` en verde sobre el head exacto ya fusionado con main):

- [PR #15](https://github.com/bfigueroa99/r6-replay-lab/pull/15), ficha 30, tests de `round_end` y del reloj del defuser -> main ff0d388.
- [PR #16](https://github.com/bfigueroa99/r6-replay-lab/pull/16), ficha 31, tests de 1vX, headshots y agregado por partida -> main 6ec5961 (main fusionado en la rama antes, `check.sh` en verde con 392 tests).

## Orden de merge sugerido

1. `claude/equipo-dev/32-days-enorme-da-500`: no choca con main 6ec5961 (merge de prueba limpio). Libera `backend/replays/views.py` y `backend/tests/test_api.py`. Espera la QA de una tercera sesion (QA de las 18:01 UTC; o P7 si pasa 48 h).

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|
| [32. Un ?days= enorme da 500 en nueve endpoints](32-days-enorme-da-500.md) | en curso (rama 32, revisado) | 2 | backend | - |

Papel: 0 propuesto, 0 disenado. Las fichas 30 y 31 ya estan en main; su espejo se quito de esta rama. El PO tiene dos candidatos anotados en las fichas 30 y 31 (abajo), pero los dos esperan una decision tuya.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-09 00:02 | Entrega y mergea 30 (PR #15) y 31 (PR #16): `## PR`, fichas recortadas, `check.sh` en verde sobre cada head exacto (380 y 392 tests backend, 53 vitest, build, 17 e2e). Ninguna rama en conflicto con main. No pudo borrar las ramas mergeadas: el proxy de git corta el push de borrado. |
| revisor | 2026-10-08 21:02 | Revisa 32 (revision ciega + confirmacion propia): sin hallazgos; otros caminos de fecha desde la query string sin 500; dos mutaciones caen. `check.sh` en verde (369 backend, 53 frontend, build, 17 e2e). 32 -> `revisado`. |
| dev | 2026-10-08 15:02 | Sin fichas tomables (30 y 31 en `revisado`, papel vacio): bug real encontrado probando parametros borde sobre `seed_demo`. `?days=1000000` daba 500 en 10 endpoints (`OverflowError` en `_filters`). Ficha 32 escrita, arreglada (1 linea + 3 tests) y dejada en `implementado`. |
| qa | 2026-10-08 18:02 | QA de 30 y 31: `check.sh` en verde sobre cada rama, 10 mutaciones propias por ficha. Dos mutantes sobrevivian y quedaron cubiertos con un test de borde cada uno: Y9S4 fuera de modo bomba (30) y compañero muerto por `DEATH` sin asesino en el 1vX (31). Las dos -> `aprobado`. |
| arquitecto | 2026-10-08 06:02 | Disena 30 y 31 con los numeros corridos contra main dc0188b. Corrige dos criterios de la PO (el reloj del defuser agrega dos START; el 1v1 necesita otro escenario). Deja dos avisos en las fichas: bug de doble ganador en Y9S4 y 1vX que se pierde con un `PLAYER_LEAVE`. |
| po | 2026-10-08 03:02 | Propone 30 y 31 (tests de `round_end`, reloj del defuser, 1vX y stats por partida; criterios verificados contra main dc0188b). |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`send-pack: unexpected disconnect while reading sideband packet`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador) y #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo en `## Para el equipo`.
  - **Bug en `round_end` (aviso de la ficha 30, ya en main):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada (30 y 31 solo agregan tests).
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo`.
  - **Bug en `round_end` (aviso de la ficha 30):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
