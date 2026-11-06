# 95. Partida anterior y siguiente, y flechas para cambiar de ronda

estado: en curso (espejo; manda la rama)
candado: -
rama: claude/equipo-dev/95-partida-anterior-y-siguiente
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: F17 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05, rama `claude/dazzling-einstein-w3qcyq` como referencia, decision del humano en `## Para el equipo` del 2026-11-05)
archivos: backend/replays/views.py, backend/tests/test_partida_anterior_y_siguiente.py, frontend/e2e/partida-sin-rondas.json, frontend/src/navegacionRondas.js, frontend/src/navegacionRondas.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/navegar-partidas.spec.js
turnos: po 20261106T0041Z-cSxDY1g, arquitecto 20261106T0109Z-cMAPx7f

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Revisar una sesion de partidas hoy obliga a volver al listado entre una y
otra, y cambiar de ronda dentro del detalle es solo con el mouse. Con esto,
desde el detalle de una partida se pasa a la anterior o a la siguiente con
un enlace, y las rondas se recorren con las flechas del teclado.

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` suma `prev_id` y `next_id`: la partida
      inmediatamente anterior y posterior por `Match.date` (desempate por
      `id`, el mismo orden que el listado de `/api/matches/`), o `null`
      en los extremos. Test de Django con tres partidas: la del medio trae
      las dos, la primera trae `prev_id: null`, la ultima `next_id: null`,
      y dos partidas con la misma fecha no se saltan ni se repiten.
- [ ] `MatchDetail.jsx` muestra enlaces "← Partida anterior" y "Partida
      siguiente →" (deshabilitados o ausentes en los extremos) que llevan a
      `/partidas/<id>`; al navegar, la ronda elegida vuelve a la primera y
      la pagina no queda con datos de la partida previa.
- [ ] En el detalle, las flechas izquierda y derecha del teclado cambian la
      ronda seleccionada (sin pasarse de la primera ni de la ultima) y no
      actuan mientras el foco esta en un campo de texto o un select. La
      logica de "ronda siguiente/anterior con tope" vive en una funcion pura
      con test de vitest.
- [ ] El e2e de `frontend/e2e/` abre una partida de `seed_demo`, sigue
      "Partida siguiente" y comprueba que cambia el titulo, y aprieta la
      flecha derecha y comprueba que cambia la ronda marcada, sin errores en
      la consola.

## Fuera de alcance

- Navegar respetando los filtros globales (tipo de partida, mapa, fechas):
  el orden es el del historial completo. Si se quiere, va despues de A10
  (ficha 96), cuando los filtros vivan en la URL.
- Atajos para cambiar de partida con el teclado (solo enlaces).
- Cualquier cambio a la timeline o a los paneles del detalle.

## Diseno

(arquitecto 20261106T0109Z-cMAPx7f)

Una sola forma obvia: sin arena ni consenso. Skills: no aplica (ni grafico
ni tabla nuevos; un listener de teclado y dos enlaces).

### Decisiones

- **"Anterior" = jugada antes** (mas vieja), "siguiente" = jugada despues.
  El listado muestra la mas nueva arriba, asi que en Partidas "siguiente"
  es la fila de arriba; los textos lo dejan claro: "← Partida anterior" y
  "Partida siguiente →" con `title` "Jugada antes" / "Jugada después".
- **Orden total `(played_at, id)`.** `Match.Meta.ordering = ["-played_at"]`
  no desempata y la ficha pide que dos partidas con la misma fecha no se
  salten ni se repitan. El desempate por `id` va en la consulta de vecinos y
  tambien en `match_list` (`qs.order_by("-played_at", "-id")` en la vista,
  despues de los filtros y antes del slice): no en `match_queryset`, que
  otras funciones agregan con `values().annotate()` y un `order_by` explicito
  entraria al GROUP BY.
- **Historial completo**, sin filtros (fuera de alcance de la ficha) e
  incluidas las partidas excluidas de la 79: navegar no es agregar.
- **Al cambiar de partida se remonta el detalle.** La ruta `/partidas/:id`
  reusa el mismo componente: `selected` quedaria en la ronda 7 y `useApi`
  mantiene `data` viejo mientras carga (`loading && !data`). Con
  `key={id}` el estado entero vuelve a cero y la pagina muestra `Loading`
  en vez de la partida previa.
- **Teclas:** solo `ArrowLeft` / `ArrowRight` sin modificadores (Alt+←
  es "Atras" del navegador; Ctrl/Meta/Shift tampoco), y nada si el foco
  esta en `INPUT`, `TEXTAREA`, `SELECT` o un elemento `contenteditable`.
  Con una tecla tomada se hace `preventDefault` (la flecha no desplaza la
  pagina); con una ignorada, no.

### Archivos

- `backend/replays/views.py`, `match_detail`: despues de obtener `match`,
  ```python
  anterior = (Match.objects.filter(Q(played_at__lt=match.played_at)
              | Q(played_at=match.played_at, id__lt=match.id))
              .order_by("-played_at", "-id").values_list("id", flat=True).first())
  siguiente = (Match.objects.filter(Q(played_at__gt=match.played_at)
               | Q(played_at=match.played_at, id__gt=match.id))
               .order_by("played_at", "id").values_list("id", flat=True).first())
  ```
  y dentro de `"match": {...}` las claves `"prev_id": anterior` y
  `"next_id": siguiente`. En `match_list`, el `order_by("-played_at", "-id")`
  de arriba con un comentario de por que.
- `backend/tests/test_partida_anterior_y_siguiente.py` (nuevo), con
  `make_match(index=...)` (fechas distintas por `index`) y `played_at=` fijo
  para los empates:
  - `test_la_partida_del_medio_trae_anterior_y_siguiente`
  - `test_la_primera_no_tiene_anterior_y_la_ultima_no_tiene_siguiente`
  - `test_dos_partidas_con_la_misma_fecha_no_se_saltan_ni_se_repiten`:
    tres partidas, dos con el mismo `played_at`; recorrer `next_id` desde
    la primera visita las tres una vez cada una, y `prev_id` desde la ultima
    lo mismo al reves.
  - `test_una_sola_partida_no_tiene_vecinas`
  - `test_el_listado_desempata_por_id`: dos partidas con la misma fecha
    salen en `/api/matches/` en orden `-id`, el mismo que siguen
    `prev_id`/`next_id`.
  - `test_partida_sin_rondas.py` compara el detalle entero con
    `frontend/e2e/partida-sin-rondas.json`: regenerar ese json (trae
    `prev_id: null` y `next_id: null`, es la unica partida del test) como dice
    el comentario de `humo.spec.js`. La 92 tambien lo toca: si se mergea
    antes, regenerar despues de mergear dev.
- `frontend/src/navegacionRondas.js` (nuevo, logica pura):
  - `rondaVecina(actual, total, paso)`: `Math.min(Math.max(actual + paso, 0), total - 1)`;
    con `total <= 0` devuelve `0`.
  - `pasoDeTecla(evento)`: `-1` para `ArrowLeft`, `1` para `ArrowRight`,
    `0` si hay `altKey`, `ctrlKey`, `metaKey` o `shiftKey`, si
    `evento.target` es `INPUT`/`TEXTAREA`/`SELECT` o `isContentEditable`, o
    cualquier otra tecla.
- `frontend/src/navegacionRondas.test.js` (vitest): no se pasa de la
  primera ni de la ultima; total 0; cada modificador da 0; foco en input,
  select, textarea y contenteditable da 0; otra tecla da 0.
- `frontend/src/pages/MatchDetail.jsx`:
  - `export default function MatchDetail()` pasa a leer `id` y devolver
    `<DetallePartida key={id} id={id} />`; el cuerpo actual se mueve a
    `function DetallePartida({ id })` sin otros cambios.
  - `useEffect` que agrega `keydown` en `window` y lo saca al desmontar:
    `const paso = pasoDeTecla(e); if (!paso || !total) return;` y
    `e.preventDefault(); setSelected((s) => rondaVecina(s, total, paso))`
    (el `preventDefault` evita que la flecha ademas desplace la pagina). `total = data?.rounds?.length ?? 0`
    en las dependencias. El efecto va antes de los `return` tempranos
    (reglas de hooks).
  - En la barra de `page-head`, antes de "Copiar resumen": dos `Link`
    `className="btn small"` a `/partidas/${match.prev_id}` y
    `/partidas/${match.next_id}`; en el extremo, el mismo texto en un boton deshabilitado (no un `Link`
    roto): `<button type="button" className="btn small" disabled>`, que
    ya tiene estilo (`.btn:disabled` en `styles.css`).
  - Hint del panel Rondas: "Clic en una ronda o ← → para ver su timeline."
- `frontend/e2e/navegar-partidas.spec.js` (nuevo; pagina existente pero flujo
  nuevo, en su propio spec como `stacks-rivales.spec.js`):
  1. `page.request.get('/api/matches/?limit=1')` da la mas nueva; su
     detalle (`/api/matches/<id>/`) trae `prev_id` no nulo y `next_id: null`.
  2. `goto('/partidas/<id>')`: "Partida siguiente →" deshabilitado
     (`toBeDisabled()`); clic en "← Partida anterior" lleva a
     `/partidas/<prev_id>` (`toHaveURL`), el `h1` es el de la API de esa
     partida (`map · score`) y la ronda activa (`.round-tab.active`) es `R1`.
  3. `keyboard.press('ArrowRight')`: la activa pasa a `R2`;
     `ArrowLeft` vuelve a `R1` y otra `ArrowLeft` la deja en `R1`.
  4. Clic en "Partida siguiente →" vuelve a `/partidas/<id>`. Consola limpia
     (`vigilarConsola`).
  Los ids salen de la API y no se escriben a mano: `seed_demo` es
  deterministico pero el orden de los ids no es parte del contrato.

### Orden

1. Vista + tests de Django.
2. `navegacionRondas.js` + vitest.
3. `MatchDetail.jsx` (remonte, teclas, enlaces), `npm run build`.
4. e2e.

### Que puede romperse

- El remonte con `key` resetea tambien `copia` y cualquier estado de los
  paneles del detalle: es lo buscado.
- `match_list` con orden explicito: los e2e de Partidas que leen "la primera
  fila" siguen viendo la mas nueva; solo cambia el orden entre empates.
- La 92 (stack rival, `implementado`) y la 79 tocan `MatchDetail.jsx` y
  `views.py`: **Implementar despues de que #92 se mergee** (esta en
  revision); con la 79 el choque es chico (otra zona del `page-head`): si
  la 79 entra antes, resolver juntando los botones.

### Verificacion manual

Abrir una partida, ir y volver con los enlaces, recorrer rondas con las
flechas; con el foco en un select de la pagina (si hay) las flechas no
mueven la ronda. Alt+← sigue siendo Atras del navegador.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Para el humano

(Nada por ahora.)
