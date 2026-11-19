# 121. Copiar una ronda como texto

estado: entregado
candado: -
rama: claude/equipo-dev/121-copiar-una-ronda-como-texto
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H10
archivos: frontend/src/textoRonda.js (nuevo), frontend/src/textoRonda.test.js (nuevo), frontend/src/pages/MatchDetail.jsx (componente CopiarRonda en el encabezado de la ronda), frontend/e2e/humo.spec.js
turnos: po 20261113T1603Z-cHj1H4k, arquitecto 20261113T1703Z-ctZvzXQ, dev 20261113T1733Z-cudo1Sw, revisor 20261113T1802Z-c8dAf7p, qa 20261113T1830Z-cTivbSq, release 20261113T1830Z-cTivbSq

## PR

Titulo: `[equipo-dev][frontend] Copiar una ronda como texto`

### Que cambia

En la pestaña de una ronda del detalle de partida aparece "Copiar ronda": copia
al portapapeles la ronda en texto plano (mapa, ronda, lado, sitio, resultado y
una linea por baja con reloj, autor, victima y las marcas apertura, entry, HS y
tradeada de la timeline), lista para pegar en Discord. Sin portapapeles avisa
que no se pudo copiar, como "Copiar resumen".

### Por que esto y no otra cosa

Ficha 121 (ALCANCE H10, epica exportar). "Copiar resumen" (ficha 66) copia la
partida entera; revisar una ronda con el equipo pedia bajar a una. Descartado:
exportar a archivo o imagen y copiar varias rondas (fuera de alcance); backend
nuevo (la API ya trae todo).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 50c6ac708, 1239 tests backend, 385 vitest, 104 e2e.
- Tests nuevos: `frontend/src/textoRonda.test.js` (8 vitest: cabecera, tres
  bajas en orden con marcas, sin bajas, teamkill y muerte sin autor, lado/sitio/
  resultado desconocidos, sin espacio final, sin ronda, sin reloj); e2e
  `el detalle de partida copia una ronda` (cabecera, autor y victima de la
  primera baja, aviso que se va al cambiar de ronda, consola limpia).
- Verificacion manual (QA): Playwright sobre `seed_demo` mas rondas de
  `factories.py` (sin bajas, teamkill, `Death`, traded): texto igual a la
  timeline; sin portapapeles avisa; teclado, foco y contraste (12.92:1 y
  5.71:1); 4 de 4 mutantes muertos.
- OMC (diseno): plan=— · revisión=— · verificación=—
- OMC (implementacion): plan=— · revisión=3 hallazgos LOW (1 arreglado) · verificación=—
- OMC (revision): plan=— · revisión=2 hallazgos LOW (1 cubierto con test, 1 refutado) · verificación=—
- OMC (QA): plan=— · revisión=— · verificación=PASS
- Skills del repo: testing-strategy (diseno e implementacion); accessibility-review
  (QA: 0 Critical, 0 Major, 1 Minor preexistente: los avisos de copiado sin
  `aria-live`, idea en ALCANCE).

### Riesgos y lo que no entra

Solo frontend: sin migracion, `recompute`, parser ni instalador. Chunk inicial
sin cambio (200.00 kB); `MatchDetail` lazy +1.45 kB. Fuera: varias rondas,
archivo o imagen.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/partidas/1`, elegir una ronda con bajas, "Copiar
ronda" y pegar en un editor: cabecera `Club House · R1 · ataque · sitio ... ·
ganada` y una linea por baja con las marcas de la timeline. Cambiar de ronda:
el aviso "Ronda copiada" desaparece.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (idea en ALCANCE: `aria-live` en los avisos de copiado).

## Que gana quien usa la app

En la pestaña de una ronda del detalle de partida, un boton copia la ronda
en texto plano (numero, lado, sitio, resultado y la linea de tiempo con
reloj, autor, victima, HS, apertura y trade) para pegarla en Discord al
revisarla con el equipo. Hoy se copia la partida entera (ficha 66) pero no
se baja a una ronda.

## Criterios de aceptacion

- [ ] Funcion pura nueva que arma el texto desde la ronda de
      `/api/matches/<id>/` (`rounds[].events`): primera linea con mapa,
      numero de ronda, lado, sitio y resultado; una linea por baja en orden
      con reloj, autor, victima y marcas (HS, apertura, tradeada); sin HTML
      ni espacios al final de linea. Vitest con una ronda de tres bajas.
- [ ] Una ronda sin bajas copia la primera linea y "Sin bajas"; vitest.
- [ ] Los teamkills y las bajas sin autor (caidas, bomba) salen con la misma
      etiqueta que la linea de tiempo de la pagina; vitest.
- [ ] Sin `navigator.clipboard` el boton avisa que no se pudo copiar, como
      "Copiar resumen" de la partida.
- [ ] e2e: en una partida de `seed_demo`, abrir una ronda, copiar, y el
      texto copiado empieza con la linea de la ronda y contiene el nick de
      una baja de esa ronda; consola limpia.

## Fuera de alcance

- Copiar varias rondas a la vez o un rango.
- Exportar la ronda a archivo o imagen.
- Backend: `/api/matches/<id>/` ya trae todo.

## Diseno

(arquitecto 20261113T1703Z-ctZvzXQ) Solo frontend sobre `/api/matches/<id>/`:
`textoRonda.js` puro (cabecera `<mapa> · <label> · <lado> · sitio <site> ·
<resultado>`, una linea por `Kill`/`Death` ordenada por `order`, etiquetas de
`Timeline`, marcas de `marcasDeApertura`, `Sin bajas`, `null` sin ronda) y
`CopiarRonda` al final de `MatchDetail.jsx` con estado propio y
`key={round.number}`, dentro del `<h3>` de la ronda. Detalle en `git log`.

## Implementacion

(dev 20261113T1733Z-cudo1Sw) Diseno completo; un vitest extra (sin reloj).
Revision ciega: 3 LOW, 1 arreglado. `verificar.sh` VERDE 389abb4cb.

## Revision 2026-11-13 sobre 6c4a6a5

(revisor 20261113T1802Z-c8dAf7p) Aprobar. Dos ejes con `omc-code-reviewer`:
B1 (orden) refutado, la API ya ordena por `order`; T1 cubierto: el e2e exige
autor y victima. VERDE 6c4a6a575.

## QA 2026-11-13 sobre 50c6ac7

(qa 20261113T1830Z-cTivbSq) Rama sin atraso contra `origin/dev` (1de3c54) y
sin conflicto (`git merge-tree --write-tree origin/dev HEAD`: salida 0).

- **check.sh**: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 50c6ac708 en 193s: 1239 tests backend, 385 vitest, 104 e2e. Todo en verde.`
- **Chunk inicial**: `npx vite build` de `origin/dev` y de la rama: `index-*.js`
  200.00 kB en los dos (sin cambio); `MatchDetail-*.js` lazy 17.52 -> 18.97 kB.
- **Base vacia** (`SQLITE_PATH=<scratchpad>/qa121.sqlite3`, `migrate`,
  `runserver 127.0.0.1:8765`): `/api/matches/` 200, `/api/matches/1/` 404,
  `/api/matches/abc/` 404, `/api/matches/?limit=-1` 200, `/partidas/1` 200.
- **Base sembrada**: `seed_demo` (29 partidas, 203 rondas) y, con
  `tests/factories.py` (`make_round`, `make_event`) en `manage.py shell`, dos
  rondas mas en la partida 1: R9 sin bajas, lado y sitio vacios y
  `my_team_won=None`; R10 con un teamkill con HS, un `Death` sin victima, una
  baja `traded` y un `OperatorSwap`. `?until=foo` 200, `?page=-1` 200.
- **Ejercicio en Chromium** sobre `seed_demo` mas R9 (sin bajas, sin lado,
  sitio ni resultado) y R10 (teamkill con HS, `Death`, traded, `OperatorSwap`)
  de `factories.py`: R9 copia `... · lado desconocido · sitio desconocido · sin
  resultado` / `Sin bajas`; R10 copia las mismas etiquetas y chips que la
  timeline, sin el `OperatorSwap`; sin espacios finales ni `undefined`; el aviso
  se va al cambiar de ronda; sin portapapeles avisa (criterio 4); consola limpia.
- **Accesibilidad**: Tab llega al boton tras las pestañas, Enter copia, foco
  visible, rol y nombre correctos, contraste 12.92:1 y 5.71:1. Minor
  preexistente: avisos de copiado sin `aria-live` (idea en ALCANCE).
- **Mutacion**: 4 de 4 mutantes muertos (orden, `Sin bajas`, `tradeada`,
  `Death` como `Kill`).
- **omc-verifier**: PASS, 5 de 5 criterios.

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major, 1 Minor
preexistente), testing-strategy (4 de 4 mutantes muertos).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
