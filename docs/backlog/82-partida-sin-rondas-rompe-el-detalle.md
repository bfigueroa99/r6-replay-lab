# 82. Una partida sin rondas rompe el detalle de partida

estado: aprobado
candado: -
rama: claude/equipo-dev/82-partida-sin-rondas-rompe-el-detalle
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: QA 20261105T0256Z-cFRtPBc de la ficha 75 (anotado alli como "ficha 81"; el 81 lo tomo otra sesion a la vez). En dev 7a87ddc, `frontend/src/pages/MatchDetail.jsx:33`: `const round = rounds[Math.min(selected, rounds.length - 1)]` da `rounds[-1]` = `undefined` con 0 rondas, y `round.label` (`:124`) tira `TypeError`
archivos: frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, frontend/e2e/partida-sin-rondas.json, backend/tests/test_partida_sin_rondas.py
turnos: qa 20261105T0256Z-cFRtPBc, arquitecto 20261105T1303Z-cfek47z, dev 20261105T1330Z-c4QLGh8, revisor 20261105T1358Z-caeHwMj, qa 20261105T1358Z-cxcyM5F

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Una partida importada sin rondas (un `.rec` cortado o una carpeta a medias) hoy deja la pagina en blanco con un error en consola. Con el arreglo se ve la cabecera de la partida y un aviso "Esta partida no tiene rondas importadas", y el resto de la app sigue navegable.

## Criterios de aceptacion

- [x] Repro de hoy: base con una partida sin rondas (`make_match` sin `make_round`), `runserver`, abrir `/partidas/<id>`: `TypeError: Cannot read properties of undefined (reading 'label')` y sin contenido. `GET /api/matches/<id>/` responde 200 con `rounds: []`.
- [x] Con el arreglo, `/partidas/<id>` muestra la cabecera de la partida y un aviso de que no hay rondas, sin error en consola.
- [x] Una partida con rondas se ve igual que antes (el e2e existente sigue verde).
- [x] Test que lo cubre: e2e con ruta interceptada que devuelve `rounds: []`, o logica pura extraida y probada con vitest.

## Fuera de alcance

Evitar que el import guarde partidas sin rondas (es otra decision); el catch-all del SPA que responde HTML 200 a `/api/matches/foo/`.

## Diseno

(arquitecto 20261105T1303Z-cfek47z, sobre dev 696c79d. Bug chico de una forma
obvia: sin consenso ni arena.)

**Repro confirmado en el backend** (spike en el scratchpad, `make_match` sin
rondas, dev 696c79d): `GET /api/matches/<id>/` responde 200 con
`rounds: []`, `scoreboard: []`, `round_streaks: {"wins": null, "losses": null}`,
`team_trades` con ceros y `untraded_pct: null`, y `my_totals` con contadores en
0 y tasas en `null`. El backend no cambia: el arreglo es del front.

**Prioriza, no bloquea:** la 79 (en curso) toca `MatchDetail.jsx` arriba (el
`useApi` y el boton de la cabecera) y la 81 cambia textos del mismo archivo.
Choques de contexto: el que mergea segundo resuelve con P3.

### Archivos y por que

**`frontend/src/pages/MatchDetail.jsx`**

- Linea 34: `const round = rounds.length ? rounds[Math.min(selected, rounds.length - 1)] : null`.
- El `<Panel title="Rondas" ...>` (lineas 104-189) se renderiza solo con
  `round`; sin rondas va, en el mismo lugar:

  ```jsx
  <Panel title="Rondas">
    <p className="note" style={{ margin: 0 }}>
      Esta partida no tiene rondas importadas.
    </p>
  </Panel>
  ```

  Sin `hint` ("Clic en una ronda..." no aplica). La cabecera, los KPIs, la
  matriz de duelos, los trades por equipo y el scoreboard siguen
  renderizandose: con los valores de arriba ya caen en sus vacios (`pct(null)`,
  `DataTable` con `[]`, `miEquipo` cae a `match.my_team_index` porque
  `rounds.length` es 0). Si el e2e muestra otro error de consola en alguno de
  ellos, el Dev lo guarda igual (render condicional con `rounds.length`) y lo
  anota en `## Implementacion`; no hace falta otro cambio de alcance.

**`frontend/e2e/partida-sin-rondas.json`** (nuevo): el cuerpo de
`/api/matches/<id>/` de una partida sin rondas **sin la clave `match`**, es
decir `rounds`, `round_streaks`, `scoreboard`, `team_trades` y `my_totals`
tal como los devuelve el backend (generarlo con un `make_match()` y
`json.dumps(..., indent=2, ensure_ascii=False)`; la forma esta arriba). Mismo
patron que `frontend/src/casosApertura.json`, que leen el front y
`test_casos_apertura.py`: un solo archivo que ambos lados afirman.

**`backend/tests/test_partida_sin_rondas.py`** (nuevo):

- `test_el_detalle_de_una_partida_sin_rondas_responde_200`: `make_match()` sin
  `make_round`; `GET /api/matches/<id>/` da 200, y la respuesta sin `match` es
  igual a `json.loads` de
  `Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "partida-sin-rondas.json"`.
  El docstring dice por que: el e2e sirve ese archivo en lugar de la respuesta
  real; si el detalle suma o cambia una clave, este test obliga a
  actualizarlo y el e2e no queda probando una forma vieja.
  (Si la 79 ya esta en dev, `"excluded"` vive en `match` y no afecta.)

**`frontend/e2e/humo.spec.js`**, test nuevo
`una partida sin rondas muestra su cabecera y un aviso`:

Al principio del archivo (`humo.spec.js` ya importa `fs`; import attributes
quedan fuera porque el Node del PC puede ser otro):

```js
const SIN_RONDAS = JSON.parse(
  fs.readFileSync(new URL('./partida-sin-rondas.json', import.meta.url), 'utf8'),
)
```

1. `const errores = vigilarConsola(page)`.
2. El id de la primera partida con `page.request.get('/api/matches/?limit=1')`.
3. `page.route(\`**/api/matches/${id}/\`, async (route) => { const respuesta = await route.fetch(); const json = await respuesta.json(); await route.fulfill({ response: respuesta, json: { ...json, ...SIN_RONDAS } }) })`
   (mismo patron que el test de `/api/filters/`, hoy linea ~794).
4. `page.goto(\`/partidas/${id}\`)`: se ve el `h1` de la cabecera (el mapa
   de esa partida, que esta en `json.match.map`), el texto
   "Esta partida no tiene rondas importadas." y el panel "Scoreboard de la
   partida"; `page.locator('.round-tab')` tiene `toHaveCount(0)`.
5. `expect(errores).toEqual([])`.

Hoy (sin el arreglo) el paso 4 falla y la consola trae el
`TypeError ... reading 'label'`: es el test rojo que prueba el bug.

### Tests

- Backend: `test_el_detalle_de_una_partida_sin_rondas_responde_200`.
- e2e: el de arriba (rojo antes, verde despues).
- Vitest: ninguno (no se extrae logica pura: es una guarda de render).

### Orden de implementacion

1. Generar `partida-sin-rondas.json` y el test de backend; suite en verde.
2. El e2e nuevo; comprobar que falla sin el arreglo.
3. El arreglo en `MatchDetail.jsx`; `npm run build`; `check.sh` completo.

### Que puede romperse

- Una partida con rondas: `round` sale igual que antes (`rounds.length > 0`);
  los e2e del detalle existentes lo cubren.
- El JSON compartido se desactualiza cuando el detalle cambie de forma: el
  test de backend falla y se regenera; es lo buscado.
- `Copiar resumen` con 0 rondas: `textoResumenPartida` ya usa
  `data?.rounds || []`; no se prueba aparte.

### Verificacion manual en el PC

No hace falta: la nube cubre todo con el e2e. Si aparece en el PC una partida
real sin rondas (carpeta cortada), abrir su detalle y ver el aviso.

Skills: no aplica (guarda de render y e2e con `page.route`, patrones que el repo ya tiene).
Arena: no (una sola forma obvia).

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1330Z-c4QLGh8, sobre dev 696c79d.)

Quedo el diseno completo, sin desvios:

- `MatchDetail.jsx`: `round` es `null` sin rondas y el panel "Rondas" muestra
  "Esta partida no tiene rondas importadas." (sin `hint`). Cabecera, KPIs,
  matriz, trades y scoreboard no necesitaron guarda: el e2e los renderiza
  con la consola limpia.
- `frontend/e2e/partida-sin-rondas.json`: generado con `make_match()` y
  `json.dumps(indent=2, ensure_ascii=False)` de la respuesta sin `match`.
- `backend/tests/test_partida_sin_rondas.py`:
  `test_el_detalle_de_una_partida_sin_rondas_responde_200` (200, `rounds: []`
  y cuerpo igual al JSON del e2e).
- e2e `una partida sin rondas muestra su cabecera y un aviso` en
  `humo.spec.js`. Unico ajuste: `.round-tab` se cuenta dentro del panel
  "Rondas", porque la matriz de duelos usa la misma clase (con la cuenta
  global daba 2).

Test rojo antes del arreglo: `npx playwright test e2e/humo.spec.js -g "sin rondas"`
fallo con `expect(locator('h1')).toContainText("Bank")` / `element(s) not found`
(pagina en blanco por el `TypeError`). Despues del arreglo, `1 passed`.

Criterios: repro (backend 200 con `rounds: []`) -> test de backend; cabecera y
aviso sin errores de consola -> e2e nuevo; partida con rondas igual -> e2e del
detalle existentes en verde; test que lo cubre -> e2e con ruta interceptada.

Nota para quien corra el e2e en la nube: el Chromium del entorno se pasa con
`E2E_CHROMIUM=/opt/pw-browsers/chromium` (lo usa `playwright.config.js`).

Skills: no aplica (patrones del repo).
Arena: no.

OMC: plan=— · revisión=1 hallazgo LOW (1 arreglado: comentario del e2e decia "lo genera") · verificación=—

## Revision 2026-11-05 sobre 6494edd

(revisor 20261105T1358Z-caeHwMj; rama al dia con dev 696c79d, sin merge
necesario.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; diff de 4
archivos, un solo tema: sin eje de intencion ni de seguridad). Con `git diff
-w`, `MatchDetail.jsx` es la guarda de `round` y el panel alternativo; el resto
es reindentacion.

Hallazgos:

- [estilo] LOW frontend/e2e/humo.spec.js:8-9
  Que pasa: el comentario de `SIN_RONDAS` junta dos motivos (origen y
  regeneracion del JSON; `fs` en vez de import attributes) en una linea muy
  larga.
  Como reproducirlo o por que es cierto: la linea 9 pasa de lejos el ancho
  del resto del archivo.
  Arreglo sugerido: partirlo en dos comentarios cortos. No bloquea.

Confirmado por el Revisor:

- Test rojo antes del arreglo, reproducido: con `MatchDetail.jsx` de dev
  696c79d, `npx playwright test e2e/humo.spec.js -g "sin rondas"` da
  `1 failed` (`toContainText` / `element(s) not found`: pagina en blanco);
  con el de la rama, `1 passed`.
- El e2e conserva el `match` real y solo reemplaza el resto con el JSON; el
  test de backend afirma que ese JSON es la respuesta real de una partida sin
  rondas, asi que no puede quedar viejo.
- Criterios: los cuatro cubiertos (backend 200 con `rounds: []` ->
  `test_partida_sin_rondas`; cabecera y aviso sin errores de consola -> e2e
  nuevo; partida con rondas igual -> e2e del detalle existentes; test -> e2e
  con ruta interceptada).
- Diff dentro de `archivos:`; sin numeros nuevos (nada para `metricas.md`);
  texto de UI con tildes, comentarios e identificadores sin tildes; sin
  `print` ni `console.log`; sin dependencias.

check.sh: `verificar.sh` VERDE 8e0e146 (954 tests backend, 186 vitest, 60 e2e).

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=—

## QA 2026-11-05 sobre b7e2cbe

QA 20261105T1358Z-cxcyM5F. Rama fusionada con dev a9f8a28 (entro la 85; sin
conflicto) antes de probar. Scripts en el scratchpad; base aparte con
`SQLITE_PATH`.

- `verificar.sh` (check.sh completo): VERDE b7e2cbe15 en 106 s, 954 tests
  backend, 190 vitest, 61 e2e.
- Criterio 1: base con `factories.py` (2 partidas con rondas y
  `make_match(map_name='Oregon', index=9, my_score=0, opponent_score=0)` sin
  rondas, id 3), `runserver 127.0.0.1:8786`; `curl /api/matches/3/` -> 200
  JSON con `rounds: []`. Cumple.
- Criterio 2: Playwright en `/partidas/3`: `h1` "Oregon · 0-0 empate", el
  aviso "Esta partida no tiene rondas importadas." una vez, paneles Rondas,
  Matriz de duelos, Trades por equipo y Scoreboard; "Copiar resumen" copia
  "Oregon · 0-0 · empate / 2026-09-02 05:00 · Ranked / Tú: 0 bajas / 0
  muertes · K/D — ...". Consola sin errores ni warnings. Cumple.
- Criterio 3: `/partidas/1` (con rondas) igual que siempre, sin aviso, con
  sus pestañas; `/partidas` lista las 3. e2e del detalle en verde. Cumple.
- Criterio 4 y mutaciones (restaurado despues, `git status` limpio):
  (1) sin `round_streaks` en `partida-sin-rondas.json` ->
  `manage.py test tests.test_partida_sin_rondas` FAILED; (2) otro texto de
  aviso + build -> `E2E_CHROMIUM=/opt/pw-browsers/chromium npx playwright
  test e2e/humo.spec.js -g "sin rondas muestra"` falla en `humo.spec.js:415`;
  (3) `MatchDetail.jsx` de dev -> falla en `humo.spec.js:411` (pagina en
  blanco). Restaurado: 1 passed. Cumple.
- Chunk inicial igual (191 207 B); `MatchDetail` lazy 14 028 -> 14 178 B.
- Bordes vecinos: `/api/matches/999999/` 404 HTML de Django y
  `/api/matches/foo/` 200 HTML del SPA: fuera de alcance, es la ficha 84.

Veredicto: `aprobado`.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 4 criterios VERIFIED, 0 bloqueantes)

## Verificar en el PC

## Pendiente

## Para el humano
