# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-09 21:15 UTC por revisor (sesion 20261009T2101Z)
playbook: origin/claude/great-cray-7o9tvf@557a890
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/32-days-enorme-da-500 | docs/backlog/32-days-enorme-da-500.md | aprobado | 3 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/32-days-enorme-da-500?expand=1) |
| claude/equipo-dev/33-fecha-con-zona-da-500 | docs/backlog/33-fecha-con-zona-da-500.md | revisado | 0 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/33-fecha-con-zona-da-500?expand=1) |

COLA=2/3  TOTAL=2/5

Mergeados a main en el ultimo Release (00:02 UTC): PR #15 (ficha 30) y PR #16 (ficha 31).

## Orden de merge sugerido

1. `claude/equipo-dev/32-days-enorme-da-500`: `aprobado` (dev, revisor y qa de tres sesiones). Ya trae main 6ec5961 fusionado y `check.sh` en verde sobre ese head. Libera `backend/replays/views.py` y `backend/tests/test_api.py`. Lista para el Release de las 00:01 UTC.
2. `claude/equipo-dev/33-fecha-con-zona-da-500`: `revisado` (segunda revision, sesion 20261009T2101Z: aprobar, sin hallazgos; `check.sh` en verde, 396 backend). Espera QA de otra sesion (QA de las 18:01 UTC, o el Release de las 00:01 no la puede mergear todavia). Merge de prueba con main 6ec5961 y con 32 limpio. Libera `backend/replays/views.py` y `backend/tests/test_dates.py`.

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|
| [32. Un ?days= enorme da 500 en nueve endpoints](32-days-enorme-da-500.md) | en curso (rama 32, aprobado) | 2 | backend | - |
| [33. Una fecha con zona horaria en ?since= o ?until= da 500](33-fecha-con-zona-da-500.md) | en curso (rama 33, revisado) | 2 | backend | - |

Papel: 0 propuesto, 0 disenado (los espejos de 32 y 33 dicen `en curso`; la rama manda: `aprobado` y `revisado`). Las fichas 30 y 31 ya estan en main; su espejo se quito de esta rama. El PO tiene dos candidatos anotados en las fichas 30 y 31 (abajo), pero los dos esperan una decision tuya.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-09 00:02 | Entrega y mergea 30 (PR #15) y 31 (PR #16): `## PR`, fichas recortadas, `check.sh` en verde sobre cada head exacto (380 y 392 tests backend, 53 vitest, build, 17 e2e). Ninguna rama en conflicto con main. No pudo borrar las ramas mergeadas: el proxy de git corta el push de borrado. |
| revisor | 2026-10-09 21:01 | Segunda revision de 33 (ciega + confirmacion propia): hallazgo anterior corregido; DST de Santiago, bordes del calendario, `+14:00` y fracciones de 9 digitos dan 200 (24/24). Sin el arreglo, 40 errores en `test_dates`. `check.sh` en verde (396 backend, 53 vitest, build, 17 e2e). 33 -> `revisado`. |
| dev | 2026-10-09 15:02 | Corrige el hallazgo de la revision de 33: `_fecha` ignora (sin 500) una fecha con zona que se sale del rango de `datetime` al pasarla a hora local; subTest nuevo con `since=0001-01-01T00:00Z` y `until=9999-12-31T23:59-05:00`. Revision ciega aprobar, `check.sh` en verde (396 backend, 53 vitest, build, 17 e2e). 33 -> `implementado`. |
| qa | 2026-10-09 18:02 | QA de 32: main fusionado en la rama, `check.sh` en verde (395 backend, 53 vitest, build, 17 e2e) y pasos de `ci.yml` sin `.env`. Repro del 500 en main con `seed_demo`; en la rama, 12 endpoints x 10 valores de `days` en base vacia y sembrada sin ningun 500. 3 mutaciones, las 3 caen. 32 -> `aprobado`. |
| arquitecto | 2026-10-09 06:04 | Sin fichas `propuesto` que disenar ni `disenado` que revalidar: turno sin trabajo de diseno. Rama 32 sin conflicto contra main 6ec5961. Limpia de este tablero un bloque duplicado que un turno anterior habia pegado entre Para el humano y Para el equipo. |
| po | 2026-10-08 03:02 | Propone 30 y 31 (tests de `round_end`, reloj del defuser, 1vX y stats por partida; criterios verificados contra main dc0188b). |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`send-pack: unexpected disconnect while reading sideband packet`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador) y #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo, en la seccion Para el equipo.
  - **Bug en `round_end` (aviso de la ficha 30, ya en main):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada (32 solo cambia un `except` en `_filters` y agrega tests; sin migracion ni parser).
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
