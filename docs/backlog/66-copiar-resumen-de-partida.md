# 66. Copiar el resumen de una partida como texto

estado: en curso 2026-10-28
candado: dev 2026-10-28 16:10Z
rama: claude/equipo-dev/66-copiar-resumen-de-partida
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H4
archivos: frontend/src/resumenPartida.js, frontend/src/resumenPartida.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261028T1607Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Despues de una partida uno quiere pasarle al equipo como fue sin mandar
capturas. Un boton en el detalle de partida copia al portapapeles un resumen
en texto plano (mapa, marcador, resultado, tu linea de stats, rondas ganadas
por lado y tu mejor ronda) listo para pegar en el chat. No sube nada: es el
portapapeles del navegador.

## Criterios de aceptacion

- [ ] Una funcion pura (`frontend/src/`, sin React) arma el texto desde el
      payload de `/api/matches/<id>/`: primera linea `<mapa> · <marcador> ·
      <resultado>` con fecha y tipo de partida; despues bajas/muertes, K/D, HS%,
      aperturas y KST tuyos; rondas ganadas en ataque y en defensa (`n de m`);
      y la ronda con mas bajas tuyas (numero y bajas; si hay empate, la primera).
      Tests vitest con un payload armado a mano.
- [ ] Casos borde con test: partida sin bajas tuyas (no inventa "mejor
      ronda": la linea no sale), partida sin rondas de un lado, resultado
      "incompleta", nick con caracteres raros. El texto no lleva HTML ni
      markdown.
- [ ] `MatchDetail.jsx` muestra un boton "Copiar resumen" en la cabecera que
      llama a `navigator.clipboard.writeText` y avisa "Copiado" en la UI; si el
      portapapeles no esta disponible o rechaza, muestra un aviso y no tira error
      a la consola.
- [ ] El e2e abre una partida de `seed_demo`, aprieta el boton (con permiso de
      portapapeles en Chromium) y afirma que el texto copiado empieza con el mapa
      y el marcador de esa partida.
- [ ] Ninguna request nueva: el resumen sale del payload que la pagina ya
      tiene.

## Fuera de alcance

- Compartir por red, enlaces o imagenes.
- Resumen de los 10 jugadores o de la matriz de duelos (idea H5).
- Copiar señales del Coach (idea H6): otro item.

## Diseno

(Arquitecto 20261027T1605Z, sobre origin/dev 2532ed1.) Solo frontend: sin
backend, sin migracion, ninguna request nueva. Ninguna rama abierta toca
`MatchDetail.jsx`.

Skills: no aplica (funcion pura con su vitest, como `multikills.js` o
`rachas.js`; el portapapeles es `navigator.clipboard.writeText`, una linea del
navegador). Sin arena: una sola forma obvia.

**Texto exacto** (lineas unidas con `\n`, sin HTML ni markdown; cada linea
que no tiene datos no sale):

```
Club House · 4-3 · victoria
2026-08-01 20:00 · Ranked
BearF99: 8 bajas / 5 muertes · K/D 1.60 · HS 38% · aperturas 2-1 · KST 71%
Rondas ganadas: ataque 3 de 4 · defensa 1 de 3
Mejor ronda: R5, 3 bajas
```

- Linea 1: `` `${match.map} · ${match.score} · ${match.result}` `` (`result` ya
  viene en castellano: `victoria`, `derrota`, `incompleta`).
- Linea 2: `match.played_at.slice(0, 16).replace('T', ' ')` y
  `match.match_type` (lo mismo que muestra la cabecera de la pagina).
- Linea 3: `<nick>` = `username` de la fila `is_me` de la **ultima** ronda que
  la tenga (el nick con el que terminaste la partida); sin ninguna, `Tú`.
  Numeros de `my_totals`: `kills`, `deaths`, `kd` con 2 decimales, `hs_pct` y
  `kst_pct` redondeados con `%`, `opening_kills-opening_deaths`. Un null se
  escribe `—` (igual que `fmt` de `ui.jsx`, pero sin importarlo: `ui.jsx`
  trae React y la funcion tiene que quedar pura).
- Linea 4: por lado, `n de m` con `m` = rondas con `my_side` de ese lado y `n`
  = las de esas con `my_team_won === true`. Un lado sin rondas no aparece
  (`Rondas ganadas: ataque 4 de 4`); sin rondas de ningun lado, la linea no
  sale.
- Linea 5: la ronda donde tu fila `is_me` tiene mas `kills`; empate -> la
  primera en orden de `rounds`; `label` de la ronda (`R5`) y `1 baja` /
  `n bajas`. Si el maximo es 0, la linea no sale.

**Archivos:**

1. `frontend/src/resumenPartida.js` (nuevo): `export function
   textoResumenPartida(data)` que recibe el payload entero de
   `/api/matches/<id>/` (`{ match, rounds, my_totals }`) y devuelve el string.
   Tolera `rounds` vacio o ausente y `my_totals` sin claves (no tira).
2. `frontend/src/resumenPartida.test.js` (nuevo), vitest, payload armado a
   mano:
   - `arma las cinco lineas con mapa, marcador y resultado primero`
   - `una partida sin bajas tuyas no tiene mejor ronda`
   - `un lado sin rondas no aparece en la linea de rondas ganadas`
   - `una partida incompleta lo dice en la primera linea`
   - `el empate de bajas elige la primera ronda`
   - `el nick sale tal cual, sin escapar ni formatear` (nick `<b>Ñandú_*|`:
     el texto lo trae literal y no contiene otras etiquetas)
   - `sin rondas ni fila tuya no rompe` (`rounds: []` -> dos primeras lineas y
     la de stats con `Tú`)
   - `un K/D nulo se escribe con raya`
3. `frontend/src/pages/MatchDetail.jsx`: en `page-head`, el boton "Copiar
   resumen" (`className="btn small"`) al lado de "Volver" (envolver los dos en
   un `<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>`).
   Estado `const [copia, setCopia] = useState(null)` (`null | 'ok' |
   'error'`). Handler `async`: si `!navigator.clipboard?.writeText`, `'error'`;
   si no, `try { await navigator.clipboard.writeText(textoResumenPartida(data));
   setCopia('ok') } catch { setCopia('error') }`. **Nada de `console.*`** (el
   e2e falla si la consola se ensucia). Al lado del boton, `<span
   className="note">`: `Copiado` con `'ok'`, `No se pudo copiar: el navegador
   no dio acceso al portapapeles.` con `'error'`. El `useState` va arriba de
   los `return` tempranos, con los otros hooks.
4. `frontend/e2e/humo.spec.js`: test `el detalle de partida copia el resumen`:
   `await page.context().grantPermissions(['clipboard-read',
   'clipboard-write'])`; tomar la primera partida de `/api/matches/?limit=200`
   (como el test de multikills), `goto(/partidas/<id>)`, click en el boton
   `Copiar resumen`, esperar el texto `Copiado`, leer con `page.evaluate(() =>
   navigator.clipboard.readText())` y afirmar que empieza con `` `${partida.map}
   · ${partida.score} · ` `` (los dos vienen en la lista). 127.0.0.1 es
   contexto seguro, asi que el portapapeles anda sin https.

Sin fila en `docs/metricas.md`: no hay numero nuevo (todos son los del
detalle de partida, que ya tienen fila).

**Orden:** 1 + 2 -> `npm test` -> 3 -> `npm run build` -> 4 ->
`./scripts/check.sh`.

**Que puede romperse:** el e2e si Chromium no da permiso de portapapeles en
headless: `grantPermissions` lo resuelve; si aun asi falla, la alternativa es
`page.addInitScript` que reemplaza `navigator.clipboard.writeText` por uno
que guarda el texto en `window`, no tocar el codigo de la app. En Electron
`navigator.clipboard` funciona en el renderer (la ventana es `file://` o
localhost); no se verifica en la nube.

**Verificacion manual:** abrir una partida, apretar el boton, pegar en un
editor: cinco lineas, sin `<` ni `*` agregados. En Firefox con permisos
bloqueados: aparece el aviso, no hay error en la consola.

## Para el humano

(Nada por ahora.)
