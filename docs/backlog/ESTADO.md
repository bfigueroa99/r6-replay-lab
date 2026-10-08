# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-08 03:30 UTC por po (sesion 20261008T0302Z)
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
| [30. Tests de quien gana la ronda y por que](30-tests-ganador-de-ronda.md) | propuesto | 2 | parser | - |
| [31. Tests de stats por jugador: 1vX, headshots y agregado por partida](31-tests-stats-por-jugador.md) | propuesto | 3 | parser | - |

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-08 00:01 | Crea la rama backlog y este tablero. Sin fichas que mergear. |
| po | 2026-10-08 03:02 | Propone 30 y 31 (tests de `round_end`, reloj del defuser, 1vX y stats por partida; criterios verificados contra main dc0188b). |

## Para el humano

- Ramas borrables (playbook anterior, solo commit de reclamo, sin codigo): `git push origin --delete claude/confident-feynman-dc9apf`
- Playbook: sigue viviendo en `claude/great-cray-7o9tvf` (PR #11, abierto). Lo mergeas vos: toca las reglas del equipo.
- PRs abiertos que no son del equipo y no se tocan: #12 (`claude/focused-newton-w26nu4`, instalador) y #14 (`claude/dazzling-einstein-w3qcyq`, filtros en la URL).
- Preguntas abiertas:
  - **Boton de backup en Datos (deuda del #16) y `REPLAY_DIR` desde la UI (deuda del #19/#20).** Los dos necesitan un POST nuevo, y `CLAUDE.md` fija la API en tres POST (`/api/import/`, `/api/overrides/`, `/api/players/<id>/ubisoft/`). El PO no los propone hasta que digas si se puede sumar un cuarto (`POST /api/backup/`) y/o un quinto (`POST /api/config/replay-dir/`, que escribiria el `.env` de `%APPDATA%`). Contesta abajo en `## Para el equipo`.
  - **#28 (calibrar el corte de 10 rondas por operador rival)** solo se puede hacer con tu base real; en la nube no hay datos. Queda para vos o para cuando haya un export anonimizado.
- Verificar en el PC: nada.
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11 (los jobs mueren en segundos). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)
