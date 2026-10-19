# Maquinaria del equipo: pendientes del playbook

Lo que mejora el loop, no la app. Lo implementa una sesion iniciada por el
dueno sobre la rama del playbook (`claude/equipo-dev/playbook`, o `main`
cuando este mergeado), nunca la Routine: toca `scripts/equipo-dev/` y
`.claude/`, que el equipo no edita. Antes de empujar:
`bash scripts/equipo-dev/pruebas.sh` en `PRUEBAS_OK`. Estados: `pendiente`,
`hecho <sha>`, `no` (lo tacha el humano). El equipo propone items nuevos
con `pulso.sh cierre --maquinaria`, que aparecen en `ESTADO.md` bajo
`### Maquinaria propuesta por el equipo`; una sesion del dueno los pasa aca.

| id | idea | por que | tam | estado |
|---|---|---|---|---|
| M1 | Cadencia de 2 h con `turno.sh --periodo` y cron `1 */2 * * *` | Con el rol por estado un item cruza el pipeline en 6 disparos; a 2 h son 12 h en vez de 18, pero duplica el costo. Evidencia al 2026-10-13: `CICLO_7D` da mediana 33 h de la primera firma al merge (6 fichas: 21, 21, 33, 61, 73 y 79 h); 12 de 41 disparos sin rastro en 7 dias (11 seguidos el 10 y 11); los turnos con rastro cerraban a los 5 minutos de 135. Lo barato primero: el encadenado (M13) usa el tiempo que ya se paga; decidir M1 con `CICLO_7D` y `PULSO` despues de una semana de encadenado | M | pendiente |
| M2 | `puerta.sh`: la puerta de merge (a-f) como script que falla solo, `--solo b` para Revisor y QA, parseo de `turnos:` con notas entre parentesis | Hoy la puerta se verifica a mano en cada Release y un `turnos:` con `(relevo de ...)` se lee distinto en cada sesion | M | hecho 88839dc |
| M3 | `PULSO.md` en backlog con linea de arranque y de cierre por turno y `merge=union` | `TURNOS_SIN_RASTRO` ve que un disparo no dejo commit, pero no distingue un disparo perdido de una sesion que arranco y murio. `pulso.sh`; `turno.sh` escribe el arranque y `estado.sh` separa perdidos de muertos | S | hecho a157c91 |
| M4 | `estado.sh --tablero`: genera cabecera, cola, papel, alcance y ultimo turno de `ESTADO.md` y protege `## Para el equipo` | Cada turno regenera el tablero a mano. Ademas: pedidos al humano con id estable (`H<n>`), migracion del formato anterior y `pulso.sh cierre` que no escribe un tablero que pierda `## Para el equipo` | L | hecho a157c91 |
| M5 | `fichas.sh` (lint de estados, candado, rama, `turnos:`) y repo bare temporal con ramas sinteticas para probar `estado.sh` entero | Los contadores de `RESUMEN` solo se probaban contra el remoto real. `sintetico.sh` arma el remoto; `pruebas.sh` prueba de punta a punta estado, puerta, pulso, fichas, la guardia y el arranque de `rutina.md` | M | hecho a157c91 |
| M6 | ESPERA_HUMANO: las `entregado (PR pendiente de merge: ...)` ocupan como maximo un lugar de COLA | Lo que espera al humano puede llenar la cola y frenar al Dev aunque el equipo no tenga nada a medio verificar | S | hecho a157c91 |
| M7 | Notas de version desde las fichas (`notas.sh`) y `RELEASE_PENDIENTE` en `estado.sh` | Lo que llega a `main` no dejaba notas. Sin `CHANGELOG.md` a proposito: cada rama lo tocaria en el mismo lugar y chocarian; las notas salen del `## PR` de cada ficha. Lo de `release.ps1` quedo en M14 | M | hecho 7791142 |
| M8 | Partir SKILL.md en `roles/<rol>.md` | Cada turno leia ~15k tokens de especificaciones de roles que no son el suyo | M | hecho e2e2f69 |
| M9 | `deriva-docs.sh`: comandos de `manage.py`, scripts y rutas `/api/` citados en docs contra el codigo; salida 1 con archivo:linea | La deriva de docs la hacia QA a mano. Ademas `npm run`, variables de `.env.example` y cifras de tests escritas a mano (README dice 419 en dos lugares) | S | hecho 99ec49b |
| M10 | `PLAYBOOK_TOCADO_POR_EL_EQUIPO` en `== playbook`: ramas `claude/equipo-dev/*` que cambian `.claude/` o `scripts/equipo-dev/` | La puerta de merge (condicion d) lo frenaba recien en el Release; ahora lo ve el Revisor. Ademas `MERGE_DEL_HUMANO` para el resto de la lista de la condicion d | S | hecho a157c91 |
| M11 | Que nada tecnico deje al equipo empujar a `main` o a la rama del playbook | Se hizo con un hook pre-push (`pre-push.sh`, lo instala `turno.sh`) y no acotando `Bash(git push:*)` en `.claude/settings.json`: un prefijo de comando no ve el destino real (`HEAD:refs/heads/main`, `+main` y `--all` pasan igual) y una regla mal escrita trabaria al equipo sin nadie que apruebe. El hook recibe cada destino resuelto y solo actua durante un turno; `pruebas.sh` prueba nueve empujes | S | hecho 7791142 |
| M12 | Release con entorno incompleto persistente: dejar la ficha `entregado (PR pendiente de merge: entorno incompleto)` y que la regla 6 de Turnos la reintente por reloj | Con el rol por estado, una `aprobado` que el Release no puede avanzar hacia que todos los disparos fueran Release y nadie mas trabajara | S | hecho cd3b76a |
| M13 | Calibrar el encadenado despues de 7 dias: `max_roles_por_turno` (3) y `minimo_para_encadenar` (40) de `turno.sh` contra `CICLO_7D`, `PULSO` y `SALUD_ROL_OCIOSO` | Los valores salieron de la medicion de turnos de 5 minutos, no de una semana encadenando. Si el costo pesa, `max_roles_por_turno=1` vuelve al comportamiento anterior | S | pendiente |
| M14 | `release.ps1` arma el cuerpo de la Release con `notas.sh` (Git Bash) o un port a PowerShell | Hoy `release.ps1` publica notas fijas. Solo verificable en el PC | S | pendiente |
| M15 | `puerta.sh --pr <n>` que lea el PR y sus comentarios con herramientas de GitHub (c2 y e hoy salen MANUAL) | El Release confirma a mano dos de las seis condiciones | M | pendiente |
| M16 | `SALUD_INVESTIGACION`: familias de `INVESTIGACION.md` sin visita en 10 dias | El Investigador corre por reloj un dia si y uno no; si la Routine pierde esos disparos, nadie lo ve | S | pendiente |
