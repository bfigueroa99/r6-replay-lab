# Estado del equipo de desarrollo autonomo

actualizado: 2026-11-15 03:14 UTC por qa, revisor, dev (sesion 20261115T0219Z-i32143169; motivo: por estado: 2 revisado; sigue: por estado: 1 implementado; sigue: por estado: 3 disenado, lugar en cola)
playbook: origin/dev@b2991fe
rutina: TURNOS_SIN_RASTRO=5 en 48 h (~11-14T07:44Z ~11-14T11:42Z ~11-14T15:40Z ~11-14T19:38Z ~11-14T23:35Z) | 11 de 41 en 7 dias
en vacio: TURNOS_EN_VACIO=0 de 7 en 48 h | 7 de 31 en 7 dias (turnos que no dejaron otro commit que ESTADO.md)
issues: ISSUES=bfigueroa99/r6-replay-lab: 0 abiertos | pedidos 0 | en curso 0 | esperando a una persona 0 | para cerrar o verificar 0 | ignorados 0 | sin confianza 0; triados en este turno: ninguno
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/136-prorroga-marcada-en-el-detalle | docs/backlog/136-prorroga-marcada-en-el-detalle.md | con hallazgos | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/136-prorroga-marcada-en-el-detalle?expand=1) |
| claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot | docs/backlog/137-cuantas-de-tus-muertes-son-headshot.md | revisado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot?expand=1) |
| claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa | docs/backlog/138-el-sitio-con-el-que-abres-la-defensa.md | implementado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa?expand=1) |
| claude/equipo-dev/79-excluir-una-partida-de-los-agregados | docs/backlog/79-excluir-una-partida-de-los-agregados.md | entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano) | 28 | [PR #81](https://github.com/bfigueroa99/r6-replay-lab/pull/81) |

COLA=4 (tope 4)  TOTAL=4 (tope 6)
RESUMEN propuesto=6 disenado=2 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=1 aprobado=0 entregado=0 espera_humano=1 cola=4 total=4 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=102 sin_merge=no pausa=no sin_rastro_48h=5 bloqueadas=2 pedidos=0

(`implementado=0` y `revisado=0` porque este contexto firmo la 138 como dev y la 137 como revisor: las cuenta `bloqueadas=2`; para la proxima sesion son tomables.)

## Orden de merge sugerido

`git merge-tree --write-tree` por pares entre 79, 136, 137 y 138, y de cada una con `origin/dev` 4d90645 (con la 134): sin conflictos (todas salen 0).

1. `claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot` (revisado, falta QA de otra sesion). Libera la 147.
2. `claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa` (implementado, falta revision de otra sesion).
3. `claude/equipo-dev/136-prorroga-marcada-en-el-detalle` (con hallazgos: un Major de contraste en la marca de prorroga, arreglo de una regla de CSS; lo arregla un Dev de otra sesion). Libera la 140.
4. `claude/equipo-dev/79-excluir-una-partida-de-los-agregados` (PR #81, lo mergea el humano: toca `CLAUDE.md`). Libera la 83 y la 109.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:29 (101-dos-partidas-lado-a-lado 102-pool-de-operadores-por-lado 103-tira-de-rondas-en-partidas 107-sitio-que-tu-equipo-repite-tras-perderlo 110-tu-forma-contra-tu-historial 111-copiar-las-senales-del-coach 112-saltar-a-la-ronda-desde-los-records 113-repetir-o-cambiar-de-operador-tras-perder 114-que-operadores-te-abren 115-prorroga-por-lado 116-en-que-estado-de-vivos-mueres 118-ver-esas-rondas-desde-el-coach 119-mejor-y-peor-partida-de-cada-sesion 120-puesto-en-el-lobby 121-copiar-una-ronda-como-texto 122-cuando-te-toco-por-ultima-vez 123-clutches-de-tus-companeros 124-partidas-por-version-del-juego 125-teamkill-marcado-en-la-timeline 126-a-que-operador-cambias-tras-perder 127-partidas-que-van-a-prorroga 128-repetir-o-cambiar-el-spawn-tras-perder 129-filtro-de-operador-en-operadores 130-saltar-a-la-siguiente-ronda-perdida 131-rondas-que-el-equipo-gano-sin-ti 132-rivales-que-se-repiten-en-la-misma-noche 133-ventaja-numerica-tirada 134-en-que-estado-de-vivos-matas 135-partida-despues-de-perder-seguido) otros:4 (fichas que llegaron a dev en 7 dias)
- Epicas en curso: impacto: 134 en dev (PR #139), 143 propuesto. rivales: 132 en dev, 137 revisado, 147 propuesto (despues de #137). revision-de-rondas: 136 con hallazgos, 139 disenado, 140 disenado (frenada por 136). posicionamiento: 138 implementado. escuadra: 109 disenado (frenada), 141 disenado, 144 propuesto. progreso: 135 en dev, 146 propuesto. lado-y-marcador: 145 propuesto. operadores: 142 propuesto. datos: 79 entregado (PR #81), 83 disenado (frenada).
- Papel: PAPEL_TIPOS=funcionalidad:11 otros:0 (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos). Cola: COLA_TIPOS=funcionalidad:4 de 4 ramas de trabajo
- `ALCANCE.md`: ALCANCE=backlog, ideas libres: 102. Ideas nuevas de este turno: T8 (el `n` del winrate en Estado al morir y al matar) y T9 (columnas alineadas entre las dos tablas de un panel), las dos `idea (deuda)` de la QA de la 134.
- Investigacion: INVESTIGACION=backlog, ultima entrada: 2026-11-09.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): ninguna | sin entrega: ninguna
- Ciclo: CICLO=0h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 134:26 135:0 132:0 131:0 128:0 129:4 133:1 127:0 130:2 125:0)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 109-quien-te-venga | disenado | funcionalidad | escuadra | 3 | - | - |
| 136-prorroga-marcada-en-el-detalle | con hallazgos | funcionalidad | revision-de-rondas | 3 | - | - |
| 137-cuantas-de-tus-muertes-son-headshot | revisado | funcionalidad | rivales | 3 | - | - |
| 138-el-sitio-con-el-que-abres-la-defensa | implementado | funcionalidad | posicionamiento | 3 | - | - |
| 139-rondas-perdidas-sobreviviendo | disenado | funcionalidad | revision-de-rondas | 3 | - | - |
| 140-ventaja-tirada-marcada-en-el-detalle | disenado | funcionalidad | revision-de-rondas | 3 | - | - |
| 141-companeros-que-pierden-vivos | disenado | funcionalidad | escuadra | 3 | - | - |
| 142-operadores-con-los-que-mueres-solo | propuesto | funcionalidad | operadores | 3 | - | - |
| 143-quien-cierra-la-ronda | propuesto | funcionalidad | impacto | 3 | - | - |
| 144-companeros-por-lado | propuesto | funcionalidad | escuadra | 3 | - | - |
| 145-ultima-ronda-antes-del-cambio-de-lado | propuesto | funcionalidad | lado-y-marcador | 3 | - | - |
| 146-que-mapas-te-tocan | propuesto | funcionalidad | progreso | 3 | - | - |
| 147-headshots-que-recibes-por-operador-rival | propuesto | funcionalidad | rivales | 3 | - | - |
| 79-excluir-una-partida-de-los-agregados | entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano) | funcionalidad | datos | 3 | - | - |
| 83-partidas-excluidas-en-partidas-y-datos | disenado | funcionalidad | datos | 3 | - | - |

FRENADAS=3 (la 109 espera a la 79; la 140 espera a la 136; la 83 espera a la 79) | disenado que esperan a una ficha que no esta en dev: no cuentan en disenado= de RESUMEN

Espejos: 134 sale del papel (en dev); 136, 137 y 138 al dia en este turno; 79 vive en su rama, que manda.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-11-15 02:40 | (release 20261115T0219Z-i32143169, siguiendo como QA) 134: ficha recortada con `## PR`, `Entrega: 134`, VERDE 7d0820d55 (1390, 455, 121) sobre el commit exacto con dev fusionado, [PR #139](https://github.com/bfigueroa99/r6-replay-lab/pull/139) abierto y mergeado (4d90645). Borrado de la rama: denegado en esta sesion, sale en BORRAR. |
| qa | 2026-11-15 02:32 | (qa 20261115T0219Z-i32143169, por estado: 2 revisado) 136 `revisado` -> `con hallazgos`: VERDE f7a821db7 (1370, 454, 120), base sembrada con prorroga, curl de bordes, Playwright (teclado, nombres y corte pasan), 3 mutaciones caen; Major: la marca punteada de una pestaña de prorroga queda en 1,26:1 y no se ve en reposo. 134 `revisado` -> `aprobado`: VERDE 6c4fd3ef3 (1390, 455, 121), dos valores recalculados a mano iguales a la API y total = Resumen, bordes 200, Playwright sin Critical ni Major, 3 mutaciones caen, verificacion PASS (fallback del lider). |
| revisor | 2026-11-15 02:50 | (revisor 20261115T0219Z-i32143169, sigue) 137 `implementado` -> `revisado`: merge de dev (con la 134) sin conflicto, VERDE d5009f84d (1404, 459, 122); 2 sondas (jugador que cambia de equipo entre rondas, partida de un jugador) y 2 mutaciones que caen; 1 LOW (el e2e no ve numeros en la fila de compañeros: el seed no la llena). Sin subagentes: revision del lider. |
| dev | 2026-11-15 03:10 | (dev 20261115T0219Z-i32143169, sigue) 138 `disenado` -> `implementado`: `defense_opener` en `/api/positioning/defense-opener/` (2 consultas fijas), panel "El sitio con el que abres la defensa" en el Coach, 13 tests Django + 4 vitest + 1 e2e, TDD con rojo visto; VERDE 4e2a48cba (1403, 459, 122) tras un rojo de carga en `accesibilidad.spec.js` (request abortada en `/tendencias`) que no volvio. Sin subagente para la revision ciega del Dev. |
| arquitecto | 2026-11-14 03:41 | (arquitecto 20261114T0316Z-cwWsU9i, sigue) Disena 141 (`alive_in_losses` en `/api/teammates/`: por compañero habitual, perdidas juntos en que termino vivo, con tu % en esas mismas rondas; corte `VIVO_EN_PERDIDAS_MIN = 10`; consulta probada sobre `seed_demo`). Idea T7 (`seed_demo` con el feed en orden de reloj). |
| investigador | 2026-11-09 20:40 | (investigador 20261109T2004Z-cQbf8yt, reloj) Familias 1, 2, 4 y 7 con cuatro subagentes. Siete ideas nuevas con fuente abierta (B21, K13, D15, D16, F20, F21, P8) y fuentes nuevas en P3 y P5; nueve descartadas con motivo. Senal fuerte: el fork prestonwillis10 de r6-dissect decodifica arma, loadout y dano (pregunta al humano). Sin pushes de codigo. |
| po | 2026-11-14 03:44 | (po 20261114T0316Z-cwWsU9i, sigue) Propone 147 (headshots que recibes por operador rival, D20, tramo de la 137: implementar despues de #137). Reconcilia D13, E6 y F24 en dev y los espejos de 134 y 137. Ideas nuevas K16 (estado al matar de tus compañeros) y E23 (muertes por headshot en el tiempo). |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca.)

- DESTRABA: ficha 79, entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano), 28 h sin commits | frena a: 109 83 | https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/79-excluir-una-partida-de-los-agregados?expand=1
- Release: RELEASE=dev lleva 21 commits que main no tiene (promover: https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1). Al publicar: en el PC `cd frontend; npm run build`, la lista "Verificar en el PC" de abajo y `.\scripts\release.ps1`.
- Ramas borrables (el proxy de la nube corta `git push --delete`; en este turno tambien lo nego el clasificador de la sesion para la 134): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida claude/equipo-dev/67-teamkills-fuera-de-las-bajas claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado claude/equipo-dev/69-clutch-cuenta-con-abandonos claude/equipo-dev/70-mapas-por-version claude/equipo-dev/71-version-del-mapa-en-la-partida claude/equipo-dev/72-apertura-marcada-en-la-timeline claude/equipo-dev/73-catalogo-y10s4-a-y11s1 claude/equipo-dev/74-version-del-mapa-en-el-resto-de-pantallas claude/equipo-dev/75-trades-de-los-dos-equipos claude/equipo-dev/76-aperturas-sin-trade claude/equipo-dev/77-selector-de-tipo-de-partida claude/equipo-dev/78-filtros-en-el-listado-de-partidas claude/equipo-dev/80-donde-quedas-fuera-de-posicion claude/equipo-dev/81-textos-de-la-ui-sin-tildes claude/equipo-dev/82-partida-sin-rondas-rompe-el-detalle claude/equipo-dev/84-enlace-a-partida-inexistente-culpa-a-django claude/equipo-dev/85-filtro-sin-rondas-esconde-la-barra claude/equipo-dev/86-duelos-dice-0-rondas-con-rondas-sin-duelos claude/equipo-dev/87-readme-con-conteos-de-tests-viejos claude/equipo-dev/88-textos-del-backend-sin-tildes claude/equipo-dev/89-salida-del-spawn-por-mapa claude/equipo-dev/90-stacks-rivales-repetidos claude/equipo-dev/91-fases-de-la-ronda-en-la-partida claude/equipo-dev/92-stack-rival-en-la-partida claude/equipo-dev/93-operador-por-sitio claude/equipo-dev/94-racha-actual-de-partidas claude/equipo-dev/95-partida-anterior-y-siguiente claude/equipo-dev/96-filtros-en-la-url claude/equipo-dev/97-clutches-silenciosos claude/equipo-dev/98-lado-inicial-por-mapa claude/equipo-dev/99-copiar-resumen-de-sesion claude/equipo-dev/100-modo-de-juego-como-dimension claude/equipo-dev/101-dos-partidas-lado-a-lado claude/equipo-dev/102-pool-de-operadores-por-lado claude/equipo-dev/103-tira-de-rondas-en-partidas claude/equipo-dev/104-hilo-de-importacion-ensucia-otros-tests claude/equipo-dev/105-url-con-byte-nulo-tumba-la-spa claude/equipo-dev/106-ruta-unc-en-la-spa claude/equipo-dev/107-sitio-que-tu-equipo-repite-tras-perderlo claude/equipo-dev/110-tu-forma-contra-tu-historial claude/equipo-dev/111-copiar-las-senales-del-coach claude/equipo-dev/112-saltar-a-la-ronda-desde-los-records claude/equipo-dev/113-repetir-o-cambiar-de-operador-tras-perder claude/equipo-dev/114-que-operadores-te-abren claude/equipo-dev/115-prorroga-por-lado claude/equipo-dev/116-en-que-estado-de-vivos-mueres claude/equipo-dev/117-hotfix-graficos-punteados claude/equipo-dev/118-ver-esas-rondas-desde-el-coach claude/equipo-dev/119-mejor-y-peor-partida-de-cada-sesion claude/equipo-dev/120-puesto-en-el-lobby claude/equipo-dev/121-copiar-una-ronda-como-texto claude/equipo-dev/122-cuando-te-toco-por-ultima-vez claude/equipo-dev/123-clutches-de-tus-companeros claude/equipo-dev/124-partidas-por-version-del-juego claude/equipo-dev/125-teamkill-marcado-en-la-timeline claude/equipo-dev/126-a-que-operador-cambias-tras-perder claude/equipo-dev/127-partidas-que-van-a-prorroga claude/equipo-dev/128-repetir-o-cambiar-el-spawn-tras-perder claude/equipo-dev/129-filtro-de-operador-en-operadores claude/equipo-dev/130-saltar-a-la-siguiente-ronda-perdida claude/equipo-dev/131-rondas-que-el-equipo-gano-sin-ti claude/equipo-dev/132-rivales-que-se-repiten-en-la-misma-noche claude/equipo-dev/133-ventaja-numerica-tirada claude/equipo-dev/134-en-que-estado-de-vivos-matas claude/equipo-dev/135-partida-despues-de-perder-seguido
- Verificar en el PC (97): `manage.py backup`, `migrate` (0005_roundplayer_clutch_kills), `recompute --dry-run` sin filas nuevas por `clutch_kills`; en Compañeros, Silenciosos con numeros creibles (no 100 % en todas las filas).
- Calibrar con la base real (138, implementada): el corte de 5 partidas por apertura de defensa (`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto con datos sinteticos.
- Rutina: 5 disparos sin rastro en 48 h (~11-14T07:44Z ~11-14T11:42Z ~11-14T15:40Z ~11-14T19:38Z ~11-14T23:35Z); revisar el historial de la Routine del equipo (la que lleva `r6-replay-lab` en el nombre). Este turno lo lanzo una sesion de orquestacion, no la Routine.

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
- 2026-11-05 (humano, respondido en su sesion de Claude Code; llego en el disparo del PO): respuestas a `## Para el humano`.
  1. Ficha 76: "apertura devuelta" = (a), el trade del evento (lo ya disenado). No cambia nada del diseno.
  2. POST nuevos: se permiten los tres. E2 (metas personales), F2 (notas por ronda) y G2 (excluir una partida de los agregados) pasan a `idea`; cada POST entra a la lista de POST permitidos de `CLAUDE.md` cuando su ficha se disene, con las mismas reglas (local, exige `application/json`).
  3. PRs #1, #2, #3, #4, #11, #14, #22 y #24 contra `main`: cerrados sin merge, con comentario. Sus ideas vuelven a `idea` (incluidas Posicionamiento del #1 y spawn peeks del #22). Las ramas no se borraron.
  4. Promocion `dev` -> `main`: autorizada. La abre y la fusiona la sesion del humano al cerrar la tanda (~04:15 UTC); el equipo no la toca.
- 2026-11-05 02:40 (po 20261105T0230Z-c8Ahepa): registrado. (1) Ficha 76: respuesta en `## Para el humano` del espejo y de su rama (7e6415c, solo docs; la 76 ya estaba `implementado` y sin candado). (2) `ALCANCE.md`: E2, F2 y G2 en `idea`; G2 ya es la ficha 79, que pide sumar su POST a `CLAUDE.md`. (3) Ideas de los PRs cerrados en `ALCANCE.md`: A10 filtros en la URL, E14 racha actual, F15 "Ver esas rondas" desde las señales, F16 filtros en Partidas (ficha 78), F17 partida anterior/siguiente y flechas, S1 fuera de posicion (ficha 80) y S2 salida del spawn con enlace a peekabooR6; vigia e pick rate ya estaban cubiertos (I2, O5); los `mercado/*` ya estaban; #11 y #24 eran maquinaria. (4) Notas de la release y "Verificar en el PC" listos en `## Para el humano`.
