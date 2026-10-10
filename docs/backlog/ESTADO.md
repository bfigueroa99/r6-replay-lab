# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-10 06:07 UTC por arquitecto (sesion 20261010T0602Z)
playbook: origin/claude/great-cray-7o9tvf@557a890
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/33-fecha-con-zona-da-500 | docs/backlog/33-fecha-con-zona-da-500.md | revisado | 9 | sin PR, [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/main...claude/equipo-dev/33-fecha-con-zona-da-500?expand=1) |

COLA=1/3  TOTAL=1/5

Ultimo merge a main: PR #17 (ficha 32), 0b547d7, Release de las 00:02 UTC.

## Orden de merge sugerido

1. `claude/equipo-dev/33-fecha-con-zona-da-500`: `revisado` (dev y revisor ya firmaron). Espera QA de otra sesion (QA de las 18:01 UTC). Merge de prueba con main 0b547d7 limpio (ya incluye 32, que tocaba el mismo `views.py`). Libera `backend/replays/views.py` y `backend/tests/test_dates.py`.

## Papel (rama backlog)

| ficha | estado | prioridad | area | candado |
|---|---|---|---|---|
| [33. Una fecha con zona horaria en ?since= o ?until= da 500](33-fecha-con-zona-da-500.md) | en curso (rama 33, revisado) | 2 | backend | - |
| [34. Una baja que venga a dos compañeros cuenta como dos trade kills](34-trade-kill-contado-doble.md) | disenado | 2 | backend | - |
| [35. Tests de como el parser decide que equipo ataca](35-tests-lado-de-los-equipos.md) | disenado | 3 | tests | - |

Papel: 0 propuesto, 2 disenado (tope de disenado lleno). Las dos estan listas para el Dev de las 09:01 (la 34 primero: prioridad 2). Ninguna choca con la rama 33 ni entre si: 34 toca `analytics/metrics.py`, `tests/test_metrics.py`, `tests/test_recompute.py` y `docs/metricas.md`; 35 solo `tests/test_pydissect.py`. Sin migraciones.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-10 00:02 | Entrega y mergea 32 (PR #17): `## PR`, ficha recortada, `check.sh` en verde sobre el head exacto 1e6ae18 con main 6ec5961 incluido (395 backend, 53 vitest, build, 17 e2e). Merge 0b547d7. Ficha 33 (`revisado`) sin conflicto con main. No pudo borrar la rama mergeada: el proxy corta el push de borrado. |
| revisor | 2026-10-09 21:01 | Segunda revision de 33 (ciega + confirmacion propia): hallazgo anterior corregido; DST de Santiago, bordes del calendario, `+14:00` y fracciones de 9 digitos dan 200 (24/24). Sin el arreglo, 40 errores en `test_dates`. `check.sh` en verde (396 backend, 53 vitest, build, 17 e2e). 33 -> `revisado`. |
| dev | 2026-10-09 15:02 | Corrige el hallazgo de la revision de 33: `_fecha` ignora (sin 500) una fecha con zona que se sale del rango de `datetime` al pasarla a hora local; subTest nuevo con `since=0001-01-01T00:00Z` y `until=9999-12-31T23:59-05:00`. Revision ciega aprobar, `check.sh` en verde (396 backend, 53 vitest, build, 17 e2e). 33 -> `implementado`. |
| qa | 2026-10-09 18:02 | QA de 32: main fusionado en la rama, `check.sh` en verde (395 backend, 53 vitest, build, 17 e2e) y pasos de `ci.yml` sin `.env`. Repro del 500 en main con `seed_demo`; en la rama, 12 endpoints x 10 valores de `days` en base vacia y sembrada sin ningun 500. 3 mutaciones, las 3 caen. 32 -> `aprobado`. |
| arquitecto | 2026-10-10 06:02 | Disena 34 (arreglo en `annotate_trades`: las bajas vengadoras se cuentan por indice en un `set`, una vez cada una; el recompute lo hereda; 4 tests y aclaracion en `metricas.md`; confirmado con spike) y 35 (8 tests de `derive_team_roles` con lector falso y overrides temporales). Ajusta el criterio 3 de 35: un ID sin nombre **si** se anota como `Unknown(<id>)` en main, el test lo documenta asi. Rama 33 sin conflicto contra main 0b547d7. |
| po | 2026-10-10 03:01 | Propone 34 (bug: `annotate_trades` suma una trade kill por cada victima vengada, asi que una baja que venga un doble cuenta 2 y +0.6 de rating; reproducido en main 0b547d7) y 35 (tests de `derive_team_roles`, que hoy solo cubre un test que se salta sin `.rec`). Fuzz de 19 endpoints con ~50 parametros borde sobre `seed_demo`: ningun 500. Reconciliacion: nada de `backlog` esta en main; el espejo de 33 esta al dia. |

## Para el humano

- Ramas borrables (ya mergeadas o sin codigo). El turno no pudo borrarlas: el proxy de la sesion corta `git push --delete` (`fatal: the remote end hung up unexpectedly`). Pegar en tu PC:
  - `git push origin --delete claude/equipo-dev/30-tests-ganador-de-ronda` (mergeada, PR #15)
  - `git push origin --delete claude/equipo-dev/31-tests-stats-por-jugador` (mergeada, PR #16)
  - `git push origin --delete claude/equipo-dev/32-days-enorme-da-500` (mergeada, PR #17)
  - `git push origin --delete claude/confident-feynman-dc9apf` (playbook anterior, solo commit de reclamo)
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador) y #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo, en la seccion Para el equipo.
  - **Bug en `round_end` (aviso de la ficha 30, ya en main):** en Y9S4+ un `DEFUSER_DISABLE_COMPLETE` del equipo que perdio segun la cabecera deja a los **dos** equipos con `won=True`. Hay que decidir cual manda (cabecera o feed) antes de arreglarlo; el PO lo puede proponer como ficha.
  - **1vX con `PLAYER_LEAVE` (aviso de la ficha 31, ya en main):** si un compañero se desconecta, el ultimo vivo que gana 1v1 queda con `1vX == 0` porque el que se fue no cuenta como muerto. ¿Debe contar? Decision de producto; no se toca hasta que digas.
  - **Ficha 35, avisos del Arquitecto (no bloquean):** `derive_team_roles` anota tambien los IDs sin nombre como `Unknown(<id>)` en `inferredOperatorSides` (el test lo deja documentado asi; si preferis que no, es otra ficha), y en empate de puntajes ataca el equipo 0 (no se testea para no fijarlo).
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada por ahora. Cuando la 34 llegue a main, correr `python manage.py recompute --dry-run` y despues `python manage.py recompute` para corregir las trade kills contadas doble en partidas ya importadas.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
