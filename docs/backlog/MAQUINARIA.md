# Maquinaria del equipo: pendientes del playbook

Lo que mejora el loop, no la app. Lo implementa una sesion iniciada por el
dueno en una rama que sale de `dev` y entra por PR que mergea el humano,
nunca la Routine: toca `scripts/equipo-dev/` y `.claude/`, que el equipo no
edita. Antes de empujar:
`bash scripts/equipo-dev/pruebas.sh` en `PRUEBAS_OK`. Estados: `pendiente`,
`hecho <sha>`, `no` (lo tacha el humano).

| id | idea | por que | tam | estado |
|---|---|---|---|---|
| M1 | Cadencia de 2 h con `turno.sh --periodo` y cron `1 */2 * * *` | Con el rol por estado un item cruza el pipeline en 6 disparos; a 2 h son 12 h en vez de 18, pero duplica el costo: decidir con `TURNOS_SIN_RASTRO` y los tiempos de ciclo de las proximas fichas | M | pendiente |
| M2 | `puerta.sh`: la puerta de merge (a-f) como script que falla solo, `--solo b` para Revisor y QA, parseo de `turnos:` con notas entre parentesis | Hoy la puerta se verifica a mano en cada Release y un `turnos:` con `(relevo de ...)` se lee distinto en cada sesion. Primera prioridad de la proxima sesion | M | en parte: b es `independencia.sh` (629b5d5) y f es `verificar.sh --estado` (cd7a22b); a, c, d y e siguen a mano |
| M3 | `PULSO.md` en backlog con linea de arranque y de cierre por turno y `merge=union` | `TURNOS_SIN_RASTRO` ve que un disparo no dejo commit, pero no distingue un disparo perdido de una sesion que arranco y murio | S | pendiente |
| M4 | `estado.sh --tablero`: genera cabecera, cola, papel, alcance y ultimo turno de `ESTADO.md` y protege `## Para el equipo` | Cada turno regenera el tablero a mano desde la salida de `estado.sh`: es la parte mas repetida y la que mas se desvia de la plantilla | L | pendiente |
| M5 | `fichas.sh` (lint de estados, candado, rama, `turnos:`) y repo bare temporal con ramas sinteticas para probar `estado.sh` entero | Los contadores de `RESUMEN` solo se prueban contra el remoto real; un estado mal escrito en una ficha hoy no lo ve nadie hasta que un rol se confunde | M | pendiente |
| M6 | ESPERA_HUMANO: las `entregado (PR pendiente de merge: ...)` ocupan como maximo un lugar de COLA | Lo que espera al humano puede llenar la cola y frenar al Dev aunque el equipo no tenga nada a medio verificar | S | pendiente |
| M7 | `CHANGELOG.md` escrito por el Release, `RELEASE_PENDIENTE` en estado.sh, `release.ps1` leyendo las notas (solo verificable en el PC) | Lo que llega a `main` no deja notas de version; el humano arma la Release a mano desde los PRs | M | pendiente |
| M8 | Partir SKILL.md en `roles/<rol>.md` | Cada turno lee ~15k tokens de especificaciones de roles que no son el suyo | M | hecho be9b8df |
| M9 | `deriva-docs.sh`: comandos de `manage.py`, scripts y rutas `/api/` citados en docs contra el codigo; salida 1 con archivo:linea | La deriva de docs la hace QA a mano en sus turnos sin trabajo y cada vez de forma distinta | S | pendiente |
| M10 | `PLAYBOOK_TOCADO_POR_EL_EQUIPO` en `== playbook`: ramas `claude/equipo-dev/*` que cambian `.claude/` o `scripts/equipo-dev/` | La puerta de merge (condicion d) lo frena recien en el Release; verlo en `estado.sh` lo frena en el Revisor | S | pendiente |
| M11 | Acotar `Bash(git push:*)` de `.claude/settings.json` a `claude/equipo-dev/NN-*` y `backlog` | Hoy nada tecnico impide al equipo empujar a `main` o a la rama del playbook: solo el playbook lo prohibe. Una restriccion mal escrita trabaria al equipo entero, asi que se prueba con cuidado (push rechazado por el permiso, no por git) | S | pendiente |
| M12 | Release con entorno incompleto persistente: dejar la ficha `entregado (PR pendiente de merge: entorno incompleto)` y que la regla 5 de Turnos la reintente por reloj | Con el rol por estado, una `aprobado` que el Release no puede avanzar hace que todos los disparos sean Release y nadie mas trabaje | S | pendiente |
| M13 | `verificar.sh`: `check.sh` desacoplado y esperado en primer plano, en tramos que entran en una llamada a Bash | `check.sh` tarda 192 s (2026-11-01); Bash manda a segundo plano lo que pasa de 120 s y en una Routine el turno terminado es la corrida terminada | S | hecho cd7a22b |
| M14 | Contexto en `EQUIPO_SESION`, `independencia.sh` y `bloqueadas=` en `RESUMEN` | El id era el minuto: dos sesiones del mismo minuto no se distinguian y una conversacion retomada si (turno revisor 20261101T0331Z perdido entero) | M | hecho 629b5d5 |
| M15 | Arranque en llamadas de menos de 30 KB (`# leer:` de `turno.sh`) y tope de 28 KB por parte en `pruebas.sh` | Bash guarda en un archivo lo que pasa de 30 KB y muestra 2 KB: el arranque de un comando (68 KB) no dejaba ver estado ni playbook | S | hecho be9b8df |
| M16 | Recrear la Routine del equipo (lo hace el humano; pasos en `README.md`) | No existe desde el 2026-10-30 20:13 UTC: 6 disparos sin rastro el 2026-10-31 y los dos turnos siguientes fueron a mano | S | pendiente |
| M17 | Permitir `mcp__claude-code-remote__list_triggers` en `.claude/settings.json` | El paso 9 del Release busca la Routine por nombre; sin el permiso queda `sin herramientas para comparar`. Toca permisos: lo decide el humano | S | pendiente |
| M18 | Portar lo vigente del PR #24 (contra `main` desde 2026-10-13, 13 commits) sobre `dev` | Trae versiones de M2 a M5 y M8 sobre un `main` de hace dos semanas; pulso, tablero generado, `fichas.sh` y repo sintetico siguen sin existir en `dev`. Cerrarlo o no lo decide el humano | M | pendiente |
