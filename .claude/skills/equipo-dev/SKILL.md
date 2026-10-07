---
name: equipo-dev
description: Una iteracion del equipo de desarrollo autonomo de r6-replay-lab. Se corre cada 3 horas desde una rutina programada, en una sesion cloud nueva. Elige un cambio, lo implementa completo con tests, lo revisa, lo documenta y lo entrega como PR. Usar cuando la rutina lo pida o cuando alguien escriba /equipo-dev.
---

# Equipo de desarrollo: una iteracion

Sos un equipo completo trabajando en turnos de una persona: product owner,
arquitecto, dev de backend, dev de frontend, QA, revisor, redactor tecnico y
release manager. Cada rol toma el control en su fase y entrega al siguiente.
La iteracion dura una sesion y produce **como maximo un PR**.

Lo que manda, en este orden: `CLAUDE.md` (reglas duras del proyecto), este
documento (como trabaja el equipo), `docs/roadmap.md` (que hay que hacer).
Si algo de aca contradice `CLAUDE.md`, gana `CLAUDE.md`.

## Principios

1. **Terminar antes que empezar.** Los PRs abiertos del equipo se atienden
   antes de abrir trabajo nuevo. Un PR rojo o con conflictos es trabajo
   pendiente, no historia.
2. **Un cambio por iteracion, completo.** Backend + frontend + tests + docs.
   Nada de "la parte 2 viene despues" salvo que quede anotado en el roadmap.
3. **Verde o no se entrega.** `./scripts/check.sh` tiene que terminar en
   `Todo en verde.` antes de cada push. Sin excepciones ni tests saltados.
4. **Chico y verificable gana a ambicioso y a medias.** Si el diff supera las
   ~300 lineas o la sesion pasa de 90 minutos sin algo entregable, se recorta
   el alcance a lo que ya esta verde y el resto se anota.
5. **El humano mergea.** El equipo abre PRs, los mantiene verdes y responde
   comentarios. Nunca mergea, nunca empuja a `main`, nunca hace force-push.
6. **No inventar trabajo.** Si lo mejor que hay es cosmetico y sin valor para
   quien usa la app, la iteracion termina sin PR y lo dice.

## Fase 0. Arranque (release manager)

```bash
cd /home/user/r6-replay-lab 2>/dev/null || cd "$(git rev-parse --show-toplevel)"
date -u +%FT%TZ          # anotar: es el reloj de la iteracion
git fetch origin main
python3 -c "import django, zstandard" 2>/dev/null || \
    python3 -m pip install -q -r requirements.txt -r requirements-dev.txt
[ -d frontend/node_modules ] || (cd frontend && npm install --no-audit --no-fund)
```

Leer `CLAUDE.md` y `docs/roadmap.md` completos. `docs/metricas.md` y
`docs/formato-rec.md` solo si la tarea toca metricas o el parser.

Estado del equipo. Hay dos fuentes y se usan las dos:

- **Git, siempre disponible.** Las ramas del equipo son `claude/equipo-dev/*`.
  Trabajo en curso = ramas con ese prefijo que no estan mergeadas en `main`:

  ```bash
  git fetch origin 'refs/heads/claude/equipo-dev/*:refs/remotes/origin/claude/equipo-dev/*'
  git branch -r --list 'origin/claude/equipo-dev/*' --no-merged origin/main
  git log -1 --format='%ci %s' origin/claude/equipo-dev/<rama>   # ultimo commit
  git log --format='%s' origin/main -- docs/roadmap.md | head -5  # areas recientes
  git diff origin/main...origin/claude/equipo-dev/<rama> -- docs/roadmap.md | grep 'en curso'  # reclamos
  ```

- **GitHub, solo si la sesion trae las herramientas `mcp__github__*`** (repo
  `bfigueroa99/r6-replay-lab`): PRs abiertos cuyo titulo empieza con
  `[equipo-dev]`, su CI, sus conflictos y los comentarios del humano. Si las
  herramientas no estan, **no es un bloqueador y no se pierde la iteracion
  buscandolas**: el equipo trabaja con git solo, no abre PR ni mira CI, y lo
  dice en una linea del informe. No hay `gh` en las sesiones cloud.

PRs y ramas de otros (`mercado/*`, `claude/loop-*`, ramas del humano): **no se
tocan**. Se pueden leer como fuente de ideas, nada mas.

Rama de trabajo: `claude/equipo-dev/<area>-<slug>` creada desde `origin/main`
actualizado, nunca encima de otra rama del equipo. Si las instrucciones de la
sesion imponen otra rama, se usa esa, y el PR lleva el prefijo igual.

## Fase 1. Mantenimiento (release manager)

Para cada PR abierto del equipo, del mas viejo al mas nuevo:

| Estado | Que hacer |
|---|---|
| Conflicto con `main` | Checkout de su rama, `git merge origin/main`, resolver, `check.sh`, push. Merge, no rebase: la rama ya es publica. |
| CI rojo | Reproducir localmente, arreglar la causa, `check.sh`, push. "Flaky" no es diagnostico. |
| Comentario humano sin responder | Pedido chico y local: implementar y responder. Pedido grande o de diseno: responder con una propuesta concreta y no empujar codigo. |
| Verde, mergeable, sin pendientes | Nada. |
| Rama del equipo no mergeada y sin PR (la sesion que la hizo no tenia GitHub) | Si ahora hay herramientas: abrirle el PR con el titulo y cuerpo del mensaje de su ultimo commit. |

Sin herramientas de GitHub, el mantenimiento se reduce a lo que git permite:
merge de prueba de `origin/main` sobre cada rama del equipo no mergeada; si
hay conflicto, se resuelve, `check.sh` en verde y push. CI y comentarios
quedan para una iteracion que si las tenga.

Si un PR del equipo lleva mas de 14 dias sin actividad del humano, no se cierra
ni se insiste: se deja verde y se menciona en el informe final.

## Fase 2. Puerta de trabajo nuevo (product owner)

**Limite de trabajo en curso: 3.** Cuentan las ramas `claude/equipo-dev/*`
no mergeadas en `main` con algun commit en los ultimos 14 dias (tengan PR o
no) y, si hay herramientas de GitHub, los PRs abiertos `[equipo-dev]` que
vivan en otras ramas. Con 3 o mas, la iteracion termina aca con el informe.
La cola la vacia el humano mergeando, cerrando o borrando ramas; abrir mas
solo la hace menos revisable. Las ramas del equipo sin actividad en 14 dias
no cuentan, pero se listan en el informe para que el humano decida: el equipo
nunca borra ramas.

Con menos de 3, elegir **una** tarea. Fuentes, en orden de prioridad:

1. **Items sin marcar en `docs/roadmap.md`** (en `origin/main`) que no tengan
   ya un PR abierto del equipo. Se toma el primero que pase los filtros.
2. **Bugs reales**: un test que falla, un warning de deprecacion de Django o
   Python que va a romper en la proxima version, un error en consola del
   build, un endpoint que devuelve 500 con datos legitimos.
3. **Huecos de prueba**: un modulo de `analytics/` o `pydissect/` sin tests
   de sus casos borde, un endpoint sin test en `test_api.py`, logica de
   `frontend/src` sin test en `logica.test.js`.
4. **Deuda anotada**: las secciones "Lo que falta" / "Deuda" dentro de items ya
   hechos del roadmap son trabajo real que nadie priorizo. Ejemplo tipico:
   "No hay forma de cambiar `REPLAY_DIR` desde la UI".
5. **Robustez del parser** frente a los cambios de temporada documentados en
   `docs/formato-rec.md`: un `.rec` raro no puede tumbar la importacion
   completa, tiene que quedar como desconocido y seguir.
6. **Mejoras de UX chicas y verificables**: estados vacios, mensajes de error
   utiles, accesibilidad basica, consistencia entre paginas.

Filtros duros (si falla uno, la tarea se descarta sin discusion):

- Esta en los no-goals de `CLAUDE.md` o en "Ideas descartadas" del roadmap.
- Necesita datos que el `.rec` no entrega (coordenadas, armas, dano, MMR,
  asistencias atribuibles, plants/defuses exactos en temporadas nuevas).
- Necesita una dependencia nueva (backend: solo `django` y `zstandard`;
  frontend: nada que no este ya en `package.json`).
- Agrega escritura a la API fuera de `/api/import/` y de los overrides que ya
  existen, o calcula metricas al consultar en vez de al importar.
- Toca la app de Electron con `alwaysOnTop`, `transparent`,
  `setIgnoreMouseEvents` o cualquier cosa que la acerque a un overlay.
- No cabe en una iteracion (ver principio 4). Si es valiosa pero grande, se
  parte: se hace la primera mitad util y la segunda se anota como item nuevo.

Rotacion: si los ultimos 3 PRs del equipo son de la misma area (`backend`,
`frontend`, `parser`, `tests`, `docs`, `infra`), preferir otra area cuando
haya candidatos equivalentes. La app es de un jugador que la usa entera, no
solo de una capa.

Decisiones de producto que son del humano (por ejemplo, dos lecturas validas
de una metrica, o si una pantalla nueva vale la complejidad): no adivinar. Se
elige otra tarea y la pregunta va al informe final y, si hay PR, a su cuerpo.

**Reclamo.** Elegida la tarea y antes de disenar: crear la rama, anotar el
item en `docs/roadmap.md` (nuevo o existente) con `[en curso <fecha-hora UTC>]`
en su titulo, commit `Reclama: <titulo>` y push. Dos iteraciones pueden
solaparse (una que se alargo, un disparo manual); la que encuentra en otra
rama del equipo un reclamo de menos de 3 horas sobre el mismo item o la misma
zona del codigo elige otra cosa. El commit final reemplaza el reclamo por `[x]`.

## Fase 3. Diseno (arquitecto)

Antes de tocar codigo, un plan de 5 a 10 lineas que responda:

- Que archivos se tocan y por que esos.
- Que tests nuevos demuestran el cambio (nombres concretos, en espanol).
- Que puede romperse: migraciones, `recompute`, el build, el instalador.
- Como se verifica a mano ademas de la suite (que URL, que comando).
- Si hay metrica nueva: que fila va en `docs/metricas.md` y con que definicion.

Revisar como el repo ya resuelve problemas parecidos antes de inventar otra
forma: `aggregates.py` para agregados, `metrics.py` para columnas por ronda,
`ui.jsx` para componentes, `logica.test.js` para logica de frontend.

## Fase 4. Implementacion (devs)

- Tests primero cuando es logica pura (metricas, parser, agregados).
- Si backend y frontend son independientes, se pueden implementar en paralelo
  con dos subagentes (`Agent`), cada uno con su parte del plan y la
  instruccion de no tocar los archivos del otro. El revisor despues los ve
  juntos.
- Estilo del repo: nombres, comentarios y docstrings en espanol sin tildes;
  textos de UI con tildes y enie; comentarios que explican por que.
- Migraciones: si hay columna nueva en `RoundPlayer`, migracion + calculo en
  `metrics.py` + `recompute` tiene que rellenarla en bases existentes.
- Sin `console.log`, `print` de debug, ni codigo comentado.

## Fase 5. QA

```bash
./scripts/check.sh
```

Tiene que terminar en `Todo en verde.`. Ademas:

- Si se toco la API: levantar `python3 manage.py runserver` con una base vacia
  y pegarle a los endpoints tocados con `curl`; con datos reales no hay en la
  nube, asi que los tests con `factories.py` son la evidencia.
- Si se toco `frontend/src`: el build pasa y el chunk inicial no crece mas de
  un 10 % sin justificacion (lo imprime `vite build`).
- Si se toco el parser: `python3 manage.py test tests.test_pydissect` ademas
  de la suite, y los casos borde nuevos tienen fixture sintetica, no `.rec`
  reales (nunca entran al repo).

## Fase 6. Revision independiente (revisor)

Lanzar un subagente con el prompt de `revision.md` de esta misma carpeta y el
diff completo (`git diff origin/main...HEAD`). El revisor no conoce el plan a
proposito: solo ve el codigo y las reglas.

Con sus hallazgos:

- Bug real, regla rota, test que no prueba lo que dice: se corrige y se vuelve
  a correr `check.sh`.
- Gusto personal o cambio de alcance: se ignora y se anota en el informe si
  vale la pena como item futuro.

## Fase 7. Documentacion (redactor tecnico)

- `docs/roadmap.md`: el item queda `### N. Titulo [x]` con dos o tres lineas
  de que quedo implementado y que no. Si la tarea no venia del roadmap, se
  agrega como item nuevo con el siguiente numero libre (mirar tambien los
  numeros que proponen los PRs abiertos para no chocar) ya marcado, con el
  mismo formato que los demas. Candidatos descubiertos en el camino: items
  nuevos sin marcar, maximo dos por iteracion, cortos.
- `docs/metricas.md`: fila por cada numero nuevo que muestra la UI.
- `README.md`: solo si cambia algo que el usuario hace (comando, pantalla,
  configuracion).
- `CLAUDE.md`: solo si cambia una regla de arquitectura. Casi nunca.

## Fase 8. Entrega (release manager)

1. Commits en espanol, en presente, como los del historial: `Agrega ...`,
   `Hace configurable ...`, `Corrige ...`. Uno por cambio coherente; el
   roadmap viaja en el mismo commit que el codigo.
2. `git push -u origin <rama>`.
3. PR contra `main` con titulo `[equipo-dev][area] Titulo corto` y el cuerpo
   de `plantilla-pr.md` de esta carpeta, completo.
4. `subscribe_pr_activity` sobre el PR nuevo, para atender CI y comentarios
   mientras la sesion viva.

Sin herramientas de GitHub: el ultimo commit de la rama lleva como mensaje el
titulo del PR y el cuerpo completo de la plantilla, para que la proxima
iteracion con herramientas (o el humano, con el boton "Compare & pull
request" que GitHub muestra para ramas recien empujadas) abra el PR sin
reconstruir nada. El informe dice que la rama quedo lista y sin PR.

## Fase 9. Informe

El ultimo mensaje de la sesion es el informe de la iteracion y tiene que
entenderse solo. Formato fijo:

```
## Iteracion equipo-dev <fecha UTC>

**Entregado:** [titulo del PR](url) | nada, porque <motivo en una linea>
**Area:** backend | frontend | parser | tests | docs | infra
**Mantenimiento:** <PR #n: que se hizo> | sin PRs pendientes
**Cola del equipo:** <n> en curso (<PRs o ramas>) | abandonadas: <ramas sin actividad en 14 dias> | ninguna
**GitHub:** con herramientas | sin herramientas (rama <nombre> lista, PR pendiente de abrir)
**Descartado esta vez:** <candidato> porque <filtro que fallo>
**Para el humano:** <decision o pregunta> | nada
**Verificacion:** check.sh en verde (<n> tests backend, <n> frontend, build ok)
```

Si la iteracion termina en la fase 2 por la puerta de trabajo en curso, el
informe igual se escribe, con `Entregado: nada, cola llena`.

## Lo que el equipo nunca hace

- Mergear o cerrar PRs, propios o ajenos. Aprobar PRs.
- Empujar a `main` o a ramas que no sean la suya. Force-push. Rebase de ramas
  publicadas.
- Saltar, desactivar o borrar un test para que la suite pase.
- Agregar dependencias, servicios externos, cuentas, telemetria, red.
- Cualquier forma de overlay in-game.
- Subir archivos `.rec`, bases `.sqlite3` o `.env` al repo.
- Abrir mas de un PR por iteracion, o abrir uno con `check.sh` en rojo.
- Borrar ramas remotas, propias o ajenas.
