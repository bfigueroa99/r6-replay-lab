# Estado del equipo de desarrollo autonomo

actualizado: 2026-11-04 00:20 UTC por dev (sesion 20261104T0003Z-cmWzGBm; motivo: por estado: 1 disenado, lugar en cola)
playbook: origin/dev@ec263c3
rutina: TURNOS_SIN_RASTRO=1 en 48 h (~11-02T04:15Z) | 11 de 41 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/73-catalogo-y10s4-a-y11s1 | docs/backlog/73-catalogo-y10s4-a-y11s1.md | implementado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/73-catalogo-y10s4-a-y11s1?expand=1) |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=78 sin_merge=no pausa=no sin_rastro_48h=1 bloqueadas=1

## Orden de merge sugerido

1. `claude/equipo-dev/73-catalogo-y10s4-a-y11s1`: unica rama abierta, sin choques con dev.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:6 (64-partidas-en-el-inicio 65-presencia-y-delta-por-operador 66-copiar-resumen-de-partida 70-mapas-por-version 71-version-del-mapa-en-la-partida 72-apertura-marcada-en-la-timeline) otros:3
- Epicas en curso: temporada-y-modo: A4 (70) y A6 (71) en dev; A8 es el tramo siguiente. paridad-referencia: R1 (64) y R4 (72) en dev. datos-nuevos-del-parser: P1 (73) `implementado` en su rama.
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0 (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos). Cola: COLA_TIPOS=funcionalidad:1 de 1 ramas de trabajo.
- `ALCANCE.md`: 78 ideas libres. Ideas nuevas de este turno: A9 reglas de 3v3 Arcade, B17 lado inicial por mapa, H8 datos para reportar a un jugador, H9 partida en .zip, K10 aperturas sin trade, K11 clutches silenciosos, P7 jugadores anonimos desde Y11S3.3.
- Investigacion: ultima entrada 2026-11-03 (familias 8, 3, 5 y 6). Paridad con la referencia 79.4 / 100 (era 76.1), must 14 de 17; faltan A1 (tipo de partida), sitio con W-L y O1.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): ninguna | sin entrega: datos-nuevos-del-parser
- Ciclo: CICLO=8h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 72:7 71:38 70:8 66:4 65:6 64:8 63:12 62:8 61:32 59:12)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 73-catalogo-y10s4-a-y11s1 | en curso (espejo; en su rama: implementado) | funcionalidad | datos-nuevos-del-parser | 2 | parser | - |
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa) | bug | temporada-y-modo | 2 | backend | - |

0 `propuesto`, 0 `disenado`; la 73 paso a su rama (`implementado`, espera Revisor de otra sesion). Para el PO: el papel esta vacio (la directiva pide 3). Candidatos a ficha chica `deuda` ya anotados: que `seed_demo` escriba `opening_kill`/`opening_death`/`entry_kill` coherentes con sus eventos (hoy el chip "apertura" de la 72 contradice "1a baja" del scoreboard en los datos demo), singular "1 baja / 1 muerte" y aviso "Copiado" (66), detalles de `DeltaLado` (65). Candidato `bug`: `seed_demo` siembra Ranked 4-3 que la regla no cierra (68).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-11-03 12:25 | (mismo turno que la QA) Entrega y mergea la 69: `aprobado` -> `entregado` -> [PR #71](https://github.com/bfigueroa99/r6-replay-lab/pull/71) -> dev ec263c3. Puerta a-f cumplida: dev, revisor y qa de contextos distintos, dev 6aee89a ya en la rama, `verificar.sh` VERDE 7117f26 (873 backend, 153 vitest, 54 e2e). Espejo quitado de `backlog`. Borrar la rama: el clasificador nego `git push --delete` (queda en `BORRAR`). |
| dev | 2026-11-04 00:20 | Implementa 73 (funcionalidad p2, `disenado` -> `implementado`, 9fbef62): Solid Snake (ataque), `FortressY10` y `Y10S4`/`Y11S1` en `constants.py`; IDs sinteticos en `test_retag.py` como pedia el diseno; 6 tests en `test_pydissect.py` y `RetagCatalogoNuevoTests` (3); docs en `formato-rec.md` y README. Revision ciega: 1 LOW (comentario) arreglado. `verificar.sh` VERDE cb26bbf12 (882 backend, 153 vitest, 54 e2e). |
| revisor | 2026-11-03 08:20 | Revisa 69 (bug p2, `implementado` -> `revisado`, 761ec50). Rama ya al dia con dev 6aee89a; `verificar.sh` VERDE 42bad97 (873 backend, 153 vitest, 54 e2e). Revision a ciegas en dos ejes (estandares e intencion): ambos aprobar, 2 LOW sin bloquear (inicializacion de `one_vx` del parser que siempre se pisa; la ganancia se limita a replays anteriores a Y9S1, ya documentado). Confirmado que `Round.teams` guarda `won` desde 0001 y que los `Event` guardados traen `PlayerLeave` con `actor_name`: `recompute` alcanza sin reparsear. |
| qa | 2026-11-03 12:15 | Prueba 69 (bug p2, `revisado` -> `aprobado`) sobre d0a2649. `verificar.sh` VERDE (873 backend, 153 vitest, 54 e2e). Base de `factories` con los dos escenarios: `recompute --dry-run` 2 filas, `recompute` 2, tercera corrida sin cambios; API con `one_vx: 2`, clutch y record 2. Bordes y base vacia en 200. 4 mutaciones caen. OMC verifier: PASS (fuzz de paridad de 200.000 rondas: 0 diferencias). |
| arquitecto | 2026-11-03 16:40 | Disena 73 (`propuesto` -> `disenado`): cuatro entradas en `constants.py` (Solid Snake de ataque, `FortressY10`, `Y10S4`/`Y11S1` en `CODE_VERSIONS`), tests en `test_pydissect.py` y `RetagCatalogoNuevoTests`, docs en `formato-rec.md` y README. Hallazgo: `test_retag.py` usa justo `398899676157`/`444310693746` como IDs desconocidos; catalogarlos tumba 8 tests (spike sobre ec263c3), y moverlos a IDs sinteticos `999000000001/2` deja la suite verde. Sin arena ni consenso (forma unica), sin pushes de codigo. |
| investigador | 2026-11-03 20:17 | Familias 8 (pasada semanal: `clone` al dia con dev ec263c3, 5 filas; paridad 76.1 -> 79.4, must 14 de 17; referencia sin cambios y 0 resenas), 3, 5 y 6. Siete ideas nuevas en `ALCANCE.md` (71 -> 78 libres): A9, B17, H8, H9, K10, K11 y P7, cada una con fuente abierta. Sin pushes de codigo. |
| po | 2026-10-30 17:10 | (sesion simultanea con revisor y arquitecto; reparto P8) Propone 71 (A6: la partida dice la version del mapa en listado, detalle y resumen copiado), 72 (R4: chips "apertura" y "entry" en la timeline, `must` de la referencia) y 73 (P1: Solid Snake, FortressY10 y code versions Y10S4/Y11S1, releidos en el fork MIT `1f0cc42`; sale de la epica `sin entrega`). `ALCANCE.md`: A4 `en dev`, nuevas A7, A8, B16, K8 y K9: 71 libres (69 al empezar). Sin pushes de codigo. |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca. La lista larga anterior, con las preguntas que respondiste el 2026-10-28, esta en `git log` de este archivo: commit 440e6a1.)

- Ramas borrables (el proxy y el clasificador de la nube cortan `git push --delete`; pegar en tu PC): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida claude/equipo-dev/67-teamkills-fuera-de-las-bajas claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado claude/equipo-dev/69-clutch-cuenta-con-abandonos claude/equipo-dev/70-mapas-por-version claude/equipo-dev/71-version-del-mapa-en-la-partida claude/equipo-dev/72-apertura-marcada-en-la-timeline
- Verificar en el PC (69, en dev por PR #71): `manage.py backup`, `recompute --dry-run` (cuenta las filas de 1vX que cambian; solo partidas anteriores a Y9S1 con abandonos) y `recompute`.
- Verificar en el PC (68, en dev por PR #66): `manage.py recompute --dry-run` ("... y N partidas (resultado)", pocas) y `recompute`; esas partidas salen `incompleta` y dejan de contar en el winrate de partidas.
- Verificar en el PC (67, en dev por PR #64): `manage.py backup`, `recompute --dry-run`, `recompute` y otra vez `recompute` ("Nada que recalcular"); K/D, KPR y rating bajan solo donde hubo teamkills. El `.exe` no corre `recompute` (aviso en la ficha).
- PRs que esperan tu merge contra dev: ninguno. Promover a main cuando quieras: RELEASE=dev lleva 85 commits que main no tiene (promover: https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1).
- Verificar en el PC (66): en Electron (`npm run desktop`), "Copiar resumen" en una partida y pegar.
- Entorno cloud (qa 20261026T2004Z): `check.sh` ya elige solo el Chromium de la imagen (`E2E_CHROMIUM`); correr `npx playwright test` suelto sin esa variable falla con `Executable doesn't exist`.
- Verificar en el PC (34, 38, 47, 55; traen migracion o tocan el parser, ya en main desde el PR #62): `manage.py backup`, `migrate`, `recompute --dry-run` (sin cambios de `clutch_vs`), `recompute`; para 38, `import_replays --force <carpeta>`; para 47, `unknown_ids` y `retag --dry-run`. Detalle en cada ficha. **Despues de bajar main, `cd frontend; npm run build`.**
- Verificar en el PC (Investigador, r6-dissect #130 e idea P5): replays Y11S3 con los dos equipos ganadores en una ronda (`my_team_won` podria salir al reves) y Y11S2 con jugadores duplicados o bajas de gente que no esta. Si tenes esos `.rec`, importalos y avisa. Nuevo (2026-11-03, idea P7): el parche Y11S3.3 de hoy aplica la privacidad del jugador al scoreboard; con un replay posterior, mira en Partidas o Rivales si algun rival sale con nick generico.
- Calibrar con la base real (umbrales solo probados con datos sinteticos): 30 rondas de Tendencias (39), 10 rondas por fila de Progreso (56, bajar `COMPARE_MIN_ROUNDS_FILA` a 8 si casi nada sale), records 6/20 (44), tramos de 45 s (52), 5 partidas para "habitual" (54), `CLUTCH_SITIO_MIN` (59) y `CLUTCH_OPERADOR_MIN` (61), 5 cada uno; cortes 30/90 s de "Cuándo llega la apertura" (63, `APERTURA_TEMPRANA`/`APERTURA_TARDIA`); 3 partidas por mapa para mejor y peor mapa del Inicio (64, `MIN_PARTIDAS_MAPA`, quiza 5).
- Tests dependientes del orden (preexistente): `python manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en `VigilanteTests`; la suite completa pasa. Candidato a ficha `tests`.
- Turnos con permisos negados (po 20261019T0325Z, release 20261020T0804Z y 20261024T0804Z): el clasificador nego correr `turno.sh`/`estado.sh`; si se repite, la rutina necesita permiso para `bash` sobre `scripts/equipo-dev/*.sh`.
- PRs abiertos que no son del equipo y no se tocan: #24, #22, #14, #11 y #1-#4. La rama `claude/bold-cori-6gcxh9` (sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas, el choque lo resuelve el equipo (P3).
- Rutina: 1 disparo sin rastro en 48 h (~11-02T04:15Z); revisar el historial de la Routine del equipo (la que lleva `r6-replay-lab` en el nombre).
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11. Lo que vale es `check.sh` local. (Aviso unico.)

## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)

- 2026-10-28 (humano, respondido en una sesion de Claude Code): decisiones sobre las preguntas de `## Para el humano`.
  - Ficha 53 (teamkills): excluirlos de `kills`. Bajas, K/D, KPR, rating, 2K/3K y ACE cuentan solo rivales; los teamkills siguen en su metrica aparte (ficha 57). Va a ficha propia, con `recompute` y `metricas.md` al dia.
  - Ficha 50 / G7 (ultimo `.rec` faltante): `won=None` cuando el marcador final no cierra la partida segun `reglas_partida`; esas partidas salen de los winrates. Va a ficha propia.
  - Ficha 31 (1vX con `PLAYER_LEAVE`): si cuenta. El que se fue esta fuera de la ronda (como ya lo toma `clutch_vs`, ficha 55), asi que el ultimo vivo que gana suma su 1vX.
  - Ficha 49 (mapas rehechos): separar cada version en su propia fila ("Consulate (Y10)"), agrupando por `Match.map_id` como proponia la ficha, sin migracion. Va a ficha propia.
  - Ficha 38: sigue mandando la cabecera. Nada que cambiar.
  - Ficha 48: la frase de `CLAUDE.md` ya dice que todos los POST exigen `application/json` (PR #61, en dev). `/api/import/` sigue exigiendo JSON.
  - Release: dev promovido a main (PR #62, c9a2d6c). El `npm run build` y `release.ps1` los corre el humano en el PC.
- 2026-10-28 16:20 (dev 20261028T1607Z): leido. Son decisiones para fichas nuevas; las abre el PO en su proximo turno (el Dev no escribe fichas de funcionalidad). Nada de esto toca la 66.
- 2026-10-28 16:53 (revisor 20261028T1644Z): leido. La 66 (ahora `revisado`) no cambia por estas decisiones, salvo la fila "Mejor ronda" de `metricas.md`, que dice "teamkills incluidos": la ficha de teamkills tiene que corregirla (anotado en la 66 y en el Papel). Saque de `ESTADO.md` un bloque viejo duplicado que estaba desde 2026-10-15 entre `## Para el humano` y este bloque, con las preguntas que respondiste: `estado.sh` lo tomaba por `## Para el equipo` y no mostraba este. Las fichas nuevas las abre el PO en su proximo turno (regla 7).
- 2026-10-29 00:40 (po 20261029T0004Z): abiertas las fichas de tus decisiones: 67 (teamkills fuera de `kills`, prioridad 1), 68 (`won=None` con marcador que no cierra), 69 (1vX con `PLAYER_LEAVE`) y 70 (mapas por version, `map_id`, etiqueta "(Y10)"). Fichas 38 y 48: nada que abrir. La 49 queda descartada como bug (historia); la 70 la reemplaza como funcionalidad.
