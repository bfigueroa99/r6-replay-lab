# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-30 17:24 UTC por arquitecto (sesion 20261030T1652Z; motivo: rol siguiente que pide el pipeline (P8): el turno salia revisor por estado (1 implementado) y la 68 ya la tenia candada otra sesion simultanea; regla 9, 69 en propuesto y 0 disenado; reloj: qa, franja 6)
playbook: origin/dev@0fedc7b
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 6 de 42 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas | compare | PR |
|---|---|---|---|---|---|
| claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado | 68 (bug p2) | implementado (candado revisor 16:54, sesion simultanea) | 0 | https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado?expand=1 | no |

COLA=1/4  TOTAL=1/6
RESUMEN propuesto=1 disenado=3 en_curso=0 huerfanas=0 implementado=1 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=1 total=1 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=71 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

Una sola rama: la 68 sale de `origin/dev@0fedc7b`, sin conflicto. Libera `ingest.py`, `recompute.py` y `reglas_partida.py`. Despues de ella entra la 69 (su diseno dice "implementar despues de que #68 se mergee": comparten `recompute.py`, el comando y `test_recompute.py`). La 71 y la 72 no pisan ninguna rama abierta.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:8 (59-clutch-por-mapa-y-sitio 61-clutch-por-operador 62-cuando-matas 63-cuando-llega-la-apertura 64-partidas-en-el-inicio 65-presencia-y-delta-por-operador 66-copiar-resumen-de-partida 70-mapas-por-version) otros:1 (fichas que llegaron a dev en 7 dias)
- Epicas en curso: temporada-y-modo: A4 (70) en dev, A6 disenada (71). datos-nuevos-del-parser: P1 en papel (73), la primera funcionalidad de la epica `sin entrega`. paridad-referencia: R1 (64) en dev, R4 disenada (72), R2, R3 y R5 idea. operadores: O6 (61) y O5 (65) en dev, O1 tramo siguiente.
- Papel: PAPEL_TIPOS=funcionalidad:3 otros:1 (propuesto y disenado). Cola: COLA_TIPOS=funcionalidad:0 de 1 ramas de trabajo.
- `ALCANCE.md`: 71 ideas libres (69 al empezar el turno del PO). A4 marcada `en dev`; A6, R4 y P1 pasan a fichas 71, 72 y 73. Ideas nuevas del turno del PO (17:10): A7 modo de juego como dimension, A8 version del mapa en el resto de las pantallas por mapa, B16 el Coach mira la presion, K8 en que estado de vivos matas, K9 señal del Coach sobre los clutches. El Arquitecto (17:24) dejo en D3 que `PLAYER_LEAVE` no sale desde Y9S1 (`events.py:292`).
- Investigacion: ultima entrada 2026-10-24.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): ninguna | sin entrega: datos-nuevos-del-parser
- Ciclo: CICLO=10h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 70:8 66:4 65:6 64:8 63:12 62:8 61:32 59:12 57:12 56:12)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 68-partidas-sin-cerrar-sin-resultado | implementado (en su rama) | bug | - | 2 | backend | revisor (en su rama) |
| 69-clutch-cuenta-con-abandonos | disenado (despues de #68) | bug | - | 2 | backend | - |
| 71-version-del-mapa-en-la-partida | disenado | funcionalidad | temporada-y-modo | 2 | backend | - |
| 72-apertura-marcada-en-la-timeline | disenado | funcionalidad | paridad-referencia | 2 | frontend | - |
| 73-catalogo-y10s4-a-y11s1 | propuesto | funcionalidad | datos-nuevos-del-parser | 2 | parser | - |
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa) | bug | temporada-y-modo | 2 | backend | - |

1 `propuesto` (73), 3 `disenado` (69, 71 y 72; tope del Arquitecto alcanzado). La 68 la tiene el Revisor. Para el Dev, en orden: 71 y 72 (funcionalidad, no pisan ninguna rama abierta); la 69 espera a que la 68 se mergee. 73 (Solid Snake, Fortress Y10 y las versiones Y10S4/Y11S1, IDs releidos en el fork `1f0cc42`) espera diseno. Candidatos a ficha chica `deuda`: singular "1 baja / 1 muerte" y aviso "Copiado" que no se borra (ficha 66), los cuatro detalles de `DeltaLado` (ficha 65), y que `seed_demo` escriba `opening_kill`/`opening_death` coherentes con sus eventos (hoy 0 de 203 rondas lo son; mueve numeros del e2e; visto al disenar la 72).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-30 12:40 | (mismo turno que la QA) Entrega y mergea la 70: `aprobado` -> `entregado` -> [PR #65](https://github.com/bfigueroa99/r6-replay-lab/pull/65) -> dev 0fedc7b. Puerta a-f cumplida: dev, revisor y qa de sesiones distintas, dev 1c92273 ya en la rama, `check.sh` en verde sobre f16a36a (despues solo cambio la ficha). Espejo quitado de `backlog`. Borrar la rama: el clasificador nego `git push --delete` (queda en `BORRAR`). |
| dev | 2026-10-30 16:17 | Implementa 68 (bug p2, `disenado` -> `implementado`, 00b8f94): `reglas_partida.resultado` deja `won=None` cuando el marcador final no cierra segun la regla (Ranked 3-2, 4-3); ingest y `recompute` (con `--dry-run` y conteo "N partidas (resultado)") usan la misma funcion; fila Partidas ganadas de `metricas.md`. Revision ciega sin bloqueantes, dos menores tomados. `check.sh` en `Todo en verde.` (851 backend, 133 vitest, build, 53 e2e). Aviso para QA: `seed_demo` siembra Ranked 4-3/3-2 como victorias (no se toco). |
| revisor | 2026-10-30 08:35 | Revisa 70 (funcionalidad p2, `implementado` -> `revisado`) sobre c7548d8, dev sin moverse. `check.sh` en `Todo en verde.` (838 backend, 133 vitest, build, 53 e2e). Ciega sin hallazgos; confirmado a mano: todo `?map=` pasa por `filtro_mapa`, lados de `by_map` por `(slug, map_id)` consistentes porque `retag` renombra por `map_id` entero, etiquetas de `MAPS` sin repetir dentro de un slug. Cada criterio con test. |
| qa | 2026-10-30 12:30 | Prueba 70 (funcionalidad p2, `revisado` -> `aprobado`) sobre f16a36a. `check.sh` en `Todo en verde.` (838 backend, 133 vitest, build, 53 e2e). Base sembrada con `factories` (ConsulateY7 3/4 ataques, ConsulateY10 0/4, Kanal, Club House `map_id=0`, ronda sin bajas) y base vacia: `/api/filters/` con versiones, CSV maps/sites/spawns una fila por version (75 y 0), `?map=<id>` y `?map=<slug>` en matches y export; 16 rutas GET x 10 `?map=` borde, todas 200. Chunk +0.1 %. Mutacion: 5 de 5 caen. |
| arquitecto | 2026-10-30 17:24 | (sesion simultanea con revisor y po; reparto P8) Disena 69 (`metrics.one_vx` con `PlayerLeave` fuera de la ronda, usada por `analyse_round` y `recompute`, que suma `one_vx` a `CAMPOS`; el parser sigue a r6-dissect; paridad sin abandonos probada en un spike con 3000 rondas; implementar despues de #68; el `.rec` solo trae `PlayerLeave` antes de Y9S1), 71 (`aggregates.etiquetas_de_mapas` sobre todas las partidas del slug, usada por `match_list` y `match_detail`; tests en archivo nuevo para no esperar a la 68) y 72 (`aperturas.js` puro + `casosApertura.json` compartido por vitest y Django contra `analyse_round`, porque `seed_demo` no tiene banderas de apertura coherentes con sus eventos; e2e de la regla visible). Sin arena (no: 18 iteraciones simultaneas en un contenedor de 4 CPU, pedido del dueño; ademas, una forma obvia en cada ficha), sin migracion, sin pushes de codigo. |
| investigador | 2026-10-24 20:12 | Familia 8, primera pasada de Replica contra r6-replay.com y Aurelix (recon completo de paginas publicas, sin cuenta ni capturas): `replica/recon.md`, `features.csv` (61 filas, 21 skip con motivo), `parity.md` (76.1 / 100, must 12 de 17), resenas 0 en 8 fuentes (`feedback.md`, `fixes.md`). Epica nueva `paridad-referencia` con R1-R4 (63 -> 67 libres). Sin pushes de codigo. |
| po | 2026-10-30 17:10 | (sesion simultanea con revisor y arquitecto; reparto P8) Propone 71 (A6: la partida dice la version del mapa en listado, detalle y resumen copiado), 72 (R4: chips "apertura" y "entry" en la timeline, `must` de la referencia) y 73 (P1: Solid Snake, FortressY10 y code versions Y10S4/Y11S1, releidos en el fork MIT `1f0cc42`; sale de la epica `sin entrega`). `ALCANCE.md`: A4 `en dev`, nuevas A7, A8, B16, K8 y K9: 71 libres (69 al empezar). Sin pushes de codigo. |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca. La lista larga anterior, con las preguntas que respondiste el 2026-10-28, esta en `git log` de este archivo: commit 440e6a1.)

- Ramas borrables (el proxy y el clasificador de la nube cortan `git push --delete`; pegar en tu PC): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida claude/equipo-dev/67-teamkills-fuera-de-las-bajas claude/equipo-dev/70-mapas-por-version
- Verificar en el PC (67, en dev por PR #64): `manage.py backup`, `recompute --dry-run`, `recompute` y otra vez `recompute` ("Nada que recalcular"); K/D, KPR y rating bajan solo donde hubo teamkills. El `.exe` no corre `recompute` (aviso en la ficha).
- PRs que esperan tu merge contra dev: ninguno. Promover a main cuando quieras: RELEASE=dev lleva 35 commits que main no tiene (https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1).
- Verificar en el PC (66): en Electron (`npm run desktop`), "Copiar resumen" en una partida y pegar.
- Entorno cloud (qa 20261026T2004Z): `check.sh` ya elige solo el Chromium de la imagen (`E2E_CHROMIUM`); correr `npx playwright test` suelto sin esa variable falla con `Executable doesn't exist`.
- Verificar en el PC (34, 38, 47, 55; traen migracion o tocan el parser, ya en main desde el PR #62): `manage.py backup`, `migrate`, `recompute --dry-run` (sin cambios de `clutch_vs`), `recompute`; para 38, `import_replays --force <carpeta>`; para 47, `unknown_ids` y `retag --dry-run`. Detalle en cada ficha. **Despues de bajar main, `cd frontend; npm run build`.**
- Verificar en el PC (Investigador, r6-dissect #130 e idea P5): replays Y11S3 con los dos equipos ganadores en una ronda (`my_team_won` podria salir al reves) y Y11S2 con jugadores duplicados o bajas de gente que no esta. Si tenes esos `.rec`, importalos y avisa.
- Calibrar con la base real (umbrales solo probados con datos sinteticos): 30 rondas de Tendencias (39), 10 rondas por fila de Progreso (56, bajar `COMPARE_MIN_ROUNDS_FILA` a 8 si casi nada sale), records 6/20 (44), tramos de 45 s (52), 5 partidas para "habitual" (54), `CLUTCH_SITIO_MIN` (59) y `CLUTCH_OPERADOR_MIN` (61), 5 cada uno; cortes 30/90 s de "Cuándo llega la apertura" (63, `APERTURA_TEMPRANA`/`APERTURA_TARDIA`); 3 partidas por mapa para mejor y peor mapa del Inicio (64, `MIN_PARTIDAS_MAPA`, quiza 5).
- Tests dependientes del orden (preexistente): `python manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en `VigilanteTests`; la suite completa pasa. Candidato a ficha `tests`.
- Turnos con permisos negados (po 20261019T0325Z, release 20261020T0804Z y 20261024T0804Z): el clasificador nego correr `turno.sh`/`estado.sh`; si se repite, la rutina necesita permiso para `bash` sobre `scripts/equipo-dev/*.sh`.
- PRs abiertos que no son del equipo y no se tocan: #24, #22, #14, #11 y #1-#4. La rama `claude/bold-cori-6gcxh9` (sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas, el choque lo resuelve el equipo (P3).
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
