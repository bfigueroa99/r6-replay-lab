# Maquinaria del equipo: pendientes del playbook

Lo que mejora el loop, no la app. Lo implementa una sesion iniciada por el
dueno sobre la rama del playbook (`claude/equipo-dev/playbook`, o `main`
cuando este mergeado), nunca la Routine: toca `scripts/equipo-dev/` y
`.claude/`, que el equipo no edita. Antes de empujar:
`bash scripts/equipo-dev/pruebas.sh` en `PRUEBAS_OK`. Estados: `pendiente`,
`hecho <sha>`, `no` (lo tacha el humano).

| id | idea | por que | tam | estado |
|---|---|---|---|---|
| M1 | Cadencia de 2 h con `turno.sh --periodo` y cron `1 */2 * * *` | Con el rol por estado un item cruza el pipeline en 6 disparos; a 2 h son 12 h en vez de 18, pero duplica el costo: decidir con `TURNOS_SIN_RASTRO` y los tiempos de ciclo de las proximas fichas | M | pendiente |
| M2 | `puerta.sh`: la puerta de merge (a-f) como script que falla solo, `--solo b` para Revisor y QA, parseo de `turnos:` con notas entre parentesis | Hoy la puerta se verifica a mano en cada Release y un `turnos:` con `(relevo de ...)` se lee distinto en cada sesion. Primera prioridad de la proxima sesion | M | pendiente |
| M3 | `PULSO.md` en backlog con linea de arranque y de cierre por turno y `merge=union` | `TURNOS_SIN_RASTRO` ve que un disparo no dejo commit, pero no distingue un disparo perdido de una sesion que arranco y murio | S | pendiente |
| M4 | `estado.sh --tablero`: genera cabecera, cola, papel, alcance y ultimo turno de `ESTADO.md` y protege `## Para el equipo` | Cada turno regenera el tablero a mano desde la salida de `estado.sh`: es la parte mas repetida y la que mas se desvia de la plantilla | L | pendiente |
| M5 | `fichas.sh` (lint de estados, candado, rama, `turnos:`) y repo bare temporal con ramas sinteticas para probar `estado.sh` entero | Los contadores de `RESUMEN` solo se prueban contra el remoto real; un estado mal escrito en una ficha hoy no lo ve nadie hasta que un rol se confunde | M | pendiente |
| M6 | ESPERA_HUMANO: las `entregado (PR pendiente de merge: ...)` ocupan como maximo un lugar de COLA | Lo que espera al humano puede llenar la cola y frenar al Dev aunque el equipo no tenga nada a medio verificar | S | pendiente |
| M7 | `CHANGELOG.md` escrito por el Release, `RELEASE_PENDIENTE` en estado.sh, `release.ps1` leyendo las notas (solo verificable en el PC) | Lo que llega a `main` no deja notas de version; el humano arma la Release a mano desde los PRs | M | pendiente |
| M8 | Partir SKILL.md en `roles/<rol>.md` | Cada turno lee ~15k tokens de especificaciones de roles que no son el suyo | M | pendiente |
| M9 | `deriva-docs.sh`: comandos de `manage.py`, scripts y rutas `/api/` citados en docs contra el codigo; salida 1 con archivo:linea | La deriva de docs la hace QA a mano en sus turnos sin trabajo y cada vez de forma distinta | S | pendiente |
| M10 | `PLAYBOOK_TOCADO_POR_EL_EQUIPO` en `== playbook`: ramas `claude/equipo-dev/*` que cambian `.claude/` o `scripts/equipo-dev/` | La puerta de merge (condicion d) lo frena recien en el Release; verlo en `estado.sh` lo frena en el Revisor | S | pendiente |
