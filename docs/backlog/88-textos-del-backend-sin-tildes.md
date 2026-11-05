# 88. Textos que arma el backend (narrativa de la partida, coach) sin tildes

estado: implementado
candado: -
rama: claude/equipo-dev/88-textos-del-backend-sin-tildes
tipo: bug
epica: -
area: backend
prioridad: 4
fuente: QA 20261105T1521Z-cEexMKJ de la 81, recorriendo `/partidas/N` en Chromium con `seed_demo`. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". La 81 dejo fuera, a proposito, los textos que manda el backend
archivos: backend/replays/analytics/narrative.py, backend/replays/analytics/coach.py, backend/replays/analytics/aggregates.py, backend/tests/test_narrative.py, backend/tests/test_compare.py, backend/tests/test_textos_con_tildes.py
turnos: qa 20261105T1521Z-cEexMKJ, arquitecto 20261105T1547Z-cDskDBu, dev 20261105T1547Z-cLk3BF3

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La narrativa de cada ronda en el detalle de la partida ("A los 35s perdiste
el primer duelo: te mató Thorn.exe. Nadie la vengó.") y los consejos del
Coach se leen con sus tildes, igual que el resto de la app despues de la 81.

## Repro

Sobre dev 0861b0b:

```bash
grep -nE '"[^"]*\b(despues|mas|tambien|segun|numero|dia|sesion|perdio|gano|mato|murio|abrio|arranco|vengo)\b[^"]*"' backend/replays/analytics/coach.py backend/replays/analytics/narrative.py
```

Da ~21 lineas de cadenas visibles, entre ellas `narrative.py:64`
"te mato {asesino}", `:66` "tu equipo perdio el primer duelo ... mato a",
`:68` "abrio la ronda", `:60` "Murio {victima}" / "arranco con uno menos",
`:80` "Nadie la vengo", `:91` "la vengo ... despues", y `coach.py:212`
"sal a roamear despues". En la app: `manage.py seed_demo`, `runserver`,
`/partidas/1`: "te mato Thorn.exe. Nadie la vengo."

## Criterios de aceptacion

- [ ] Las cadenas visibles de `narrative.py` llevan tildes ("mató", "murió", "perdió", "abrió", "arrancó", "vengó", "después").
- [ ] Un barrido de las cadenas visibles de `coach.py` (titulos, consejos, textos de señales) no deja otras sin tilde; identificadores, claves (`key`/`id` de señales), comentarios y docstrings siguen sin tildes.
- [ ] `test_narrative.py`, `test_teamkills.py` y cualquier e2e que afirme estos textos se actualizan al texto nuevo, sin borrar ningun caso.
- [ ] `check.sh` en verde.

## Fuera de alcance

Reescribir textos (solo tildes); cambiar claves de señales o del JSON;
mensajes de error de la API y de los comandos de `manage.py` (no los ve la UI
salvo el de importacion, que se puede sumar si el barrido lo encuentra).

## Diseno

Arquitecto 20261105T1547Z-cDskDBu, sobre dev 0861b0b. Una sola forma obvia
(poner tildes en literales): sin arena ni consenso. El barrido de cadenas
se hizo con `ast` (constantes `str` con un espacio, sin docstrings) sobre
`coach.py`, `narrative.py`, `aggregates.py` y `views.py`; la lista de abajo
es la completa, el Dev no tiene que decidir nada.

`archivos:` `backend/replays/analytics/narrative.py`,
`backend/replays/analytics/coach.py`, `backend/replays/analytics/aggregates.py`
(solo las etiquetas de comparacion), `backend/tests/test_narrative.py`,
`backend/tests/test_compare.py`, `backend/tests/test_textos_con_tildes.py`
(nuevo). Sale `test_teamkills.py` de la lista del PO: no afirma ninguno de
estos textos (`git grep` sobre dev). Ningun e2e afirma estos textos (el
`/mato a|murio/` de `humo.spec.js:439` es la timeline que arma el frontend,
y la 81 ya lo pasa a `/mató a|murió/`).

Sumo las etiquetas de comparacion de `aggregates.py:2620` y `:2625`
("Ultimos N dias", "Ultimas N partidas"): son el mismo bug (texto del
backend que la UI muestra tal cual en Tendencias) y el barrido no encontro
otra cadena visible en `aggregates.py` ni en `views.py`. Los mensajes de
error de `views.py` siguen fuera, como dice la ficha.

### Cambios exactos

Solo tildes: ni una palabra mas ni menos. Identificadores, claves de
señales (`"fatiga-sesion"`, etc.), comentarios y docstrings no se tocan.

`narrative.py`:
- `:59` `Murio {victima}` -> `Murió {victima}`
- `:61` `arranco con uno menos` -> `arrancó con uno menos`
- `:64` `te mato {asesino}` -> `te mató {asesino}`
- `:66` `tu equipo perdio ... {asesino} mato a` -> `perdió ... mató a`
- `:68` `tu equipo abrio la ronda: {asesino} mato a` -> `abrió ... mató a`
- `:80` `Nadie la vengo` / `El rival no la vengo` -> `vengó` (las dos)
- `:91` `la vengo {..} despues` -> `la vengó {..} después`
- `:92` `Se vengo enseguida` -> `Se vengó enseguida`
- `:138` `de accion` -> `de acción`
- `:177` `se cerro por eliminacion` -> `se cerró por eliminación`
- `:179` `no expone como se cerro` -> `no expone cómo se cerró`
- `:182` `el reloj paro en` -> `el reloj paró en`

`coach.py` (numeros de linea de dev 0861b0b):
- `:59` `partidas mas` -> `partidas más`
- `:124` `Pide explicitamente` -> `Pide explícitamente`
- `:146` `usa camara` -> `usa cámara`
- `:184` `Estas jugando` -> `Estás jugando`
- `:185` `Manten esa distancia y aprovechala` -> `Mantén ... aprovéchala`
- `:206` `te estas quedando` -> `te estás quedando`
- `:212` `sal a roamear despues` -> `después`
- `:253` `informacion de nadie ... todavia agrupado` -> `información ... todavía`
- `:259` `sepas de donde vienen` -> `sepas de dónde vienen`
- `:279` `la ejecucion nunca llego` -> `la ejecución nunca llegó`
- `:281` `la informacion no este completa` -> `la información no esté completa`
- `:311` `Dedica una sesion` -> `sesión`
- `:314` `angulos y donde te paras ... que mas juegas` -> `ángulos y dónde te paras ... que más juegas`
- `:353` `Tu mecanica` -> `Tu mecánica`
- `:354` `esta en decisiones y posicion` -> `está en decisiones y posición`
- `:375` `el equipo jugo` -> `el equipo jugó`
- `:377` `buscar mas kills` -> `buscar más kills`
- `:392` `quedes ultimo ... dos angulos` -> `quedes último ... dos ángulos`
- `:421` `aprendetelo ... dos angulos ... Es mas rentable` -> `apréndetelo ... ángulos ... Es más rentable`
- `:464` `Anota que hacen ... y que pared ... con mas retorno` -> `Anota qué hacen ... y qué pared ... con más retorno`
- `:514` `Priorizalo` -> `Priorízalo`
- `:628` `esta apretado ... mas ejecucion` -> `está apretado ... más ejecución`
- `:672` `tambien bajan` -> `también bajan`
- `:679` `de cada sesion` -> `de cada sesión`
- `:682` `Fijate ... por sesion ... cuesta mas MMR ... error mecanico` -> `Fíjate ... sesión ... más ... mecánico`
- `:718` `es el angulo` -> `es el ángulo`
- `:757` `contra el: deja que alguien mas` -> `contra él: deja que alguien más`
- `:784` y `:799` `Ultimas 5 partidas` -> `Últimas 5 partidas`
- `:785` `promedio historico` -> `promedio histórico`
- `:786` `corta la sesion ... cuesta mas MMR ... error mecanico` -> `sesión ... más ... mecánico`
- `:801` `fijate un tope` -> `fíjate un tope`

Se quedan como estan (revisadas): `"Tu {lado} rinde ... que tu {otro}"`
(posesivo), `"esta persona"` (demostrativo), el ordinal `"{n}a partida"`
(cambiarlo es reescribir, no tildar), y las que ya traen tilde
(`puntería`, `posición`, `Fíjate qué haces`, `acompaña`, `compañero`).

`aggregates.py`:
- `:2620` `Ultimos {n} dias` -> `Últimos {n} días`
- `:2625` `Ultimas {..} partidas` -> `Últimas {..} partidas`

### Tests

- `test_narrative.py`: actualizar al texto nuevo las afirmaciones de las
  lineas 68, 69, 77, 88, 161 y 165 (`te mató rival`, `Nadie la vengó`,
  `El rival no la vengó`, `amigo la vengó 2s después`,
  `La ronda se cerró por eliminación.`, `no expone cómo se cerró`). Ningun
  caso se borra.
- `test_compare.py:52` y `:126`: `Últimas 4 partidas`, `Últimos 10 días`.
- Nuevo `backend/tests/test_textos_con_tildes.py`, un test:
  `test_los_textos_del_coach_y_la_narrativa_no_pierden_las_tildes`. Recorre
  con `ast` los literales `str` con al menos un espacio de `coach.py` y
  `narrative.py` (saltando docstrings de modulo, clase y funcion; las
  partes constantes de los f-strings son `ast.Constant` y entran solas) y
  falla, con archivo, linea y palabra, si alguno contiene con `\b` y sin
  distinguir mayusculas una de: `despues mas tambien sesion ultimo ultimas
  angulo angulos informacion ejecucion mecanica mecanico historico fijate
  priorizalo aprendetelo manten aprovechala camara explicitamente todavia
  mato murio perdio abrio arranco vengo cerro paro eliminacion accion jugo
  llego`. No van `esta`, `que`, `donde`, `el`, `tu`, `como` (son ambiguas y
  darian falsos positivos). El filtro "con un espacio" deja fuera las claves
  como `"fatiga-sesion"`. Ruta a los archivos con
  `Path(replays.analytics.__file__).parent` (o `coach.__file__`), sin
  Django mas alla del runner. Este test es la guardia: hoy falla con ~40
  hallazgos y tiene que pasar al terminar.

### Orden de implementacion

1. El test nuevo primero (ver que falla y que lista lo de arriba).
2. `narrative.py` y sus afirmaciones de `test_narrative.py`.
3. `coach.py`.
4. `aggregates.py` y `test_compare.py`.
5. `check.sh`.

### Que puede romperse

- Codificacion: los `.py` ya tienen `ñ` y tildes en literales
  (`coach.py:170` `compañero`) y `JsonResponse` manda UTF-8; no hace falta
  nada. Escribir los archivos en UTF-8 sin BOM.
- Un test que afirme un texto que se me escapo: lo encuentra la suite; se
  actualiza al texto nuevo, nunca se borra.
- Conflicto con la 79 en `aggregates.py`: sus hunks llegan hasta ~:2086 y
  despues :2763; las lineas 2620/2625 quedan afuera. Si la 79 entra antes,
  los numeros de linea se corren ~33; el texto a buscar es el mismo.
- Nada de metricas ni de JSON: `docs/metricas.md` no cambia.

### Verificacion manual

`manage.py seed_demo`, `runserver`, `/partidas/1`: la narrativa de la ronda
dice "te mató ... Nadie la vengó." (o la variante que toque); `/coach`:
ninguna tarjeta con "mas", "sesion", "despues"; Tendencias, comparacion:
"Últimas N partidas".

Skills: no aplica (textos en un modulo que ya existe, ningun dominio nuevo).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1547Z-cLk3BF3, sobre dev 0861b0b)

Hecha la lista completa del diseno en `narrative.py`, `coach.py` y `aggregates.py`, solo tildes: claves de señales, `metric=`, identificadores, comentarios y docstrings no cambian.

Desvios del diseno (todos en textos visibles, encontrados al recorrer con `ast` las cadenas de `coach.py` despues de aplicar la lista):
- `coach.py:312` "quien abre, quien tradea" -> "quién abre, quién tradea" (interrogativa indirecta).
- `coach.py:391` "quedandote solo" -> "quedándote solo".
- `coach.py:464` "te ganan ahi" -> "ahí".
- `coach.py:629` "ya te funciono" -> "funcionó".
- `aggregates.py:2620` tambien "Los {n} dias anteriores" -> "días" (la otra mitad de la misma tupla).
- La guardia suma `quedandote` y `ahi` a la lista del diseno, y un segundo test (`test_la_guardia_encuentra_una_palabra_sin_tilde`) para que un patron roto no pase el primero sin mirar nada.

Test que falla primero (tipo bug): `cd backend && python3 manage.py test tests.test_textos_con_tildes` sobre dev sin el arreglo -> `FAILED (failures=1)` con 57 hallazgos (`coach.py:124 'explicitamente'` ... `narrative.py:92 'vengo'`). Con el arreglo, verde.

Tests por criterio:
1. Narrativa con tildes: `test_los_textos_del_coach_y_la_narrativa_no_pierden_las_tildes` (nuevo) y los asserts de `test_narrative.py` (lineas 68, 69, 77, 88, 161, 165) pasados al texto nuevo.
2. Barrido de `coach.py`: el mismo test guardia; identificadores intactos (lo confirmo la revision ciega).
3. Tests y e2e: `test_narrative.py` y `test_compare.py` (`Últimas 4 partidas`, `Últimos 10 días`) actualizados, ningun caso borrado; ningun e2e afirma estos textos (`/mato a|murio/` de `humo.spec.js` es la timeline del frontend, ficha 81).
4. `verificar.sh`: VERDE 3c431b6 (957 tests backend, 197 vitest, 62 e2e).

Revision ciega (`omc-code-reviewer`): aprobar, 4 LOW, dejados a proposito:
- la guardia no mira `aggregates.py` (muchos docstrings y textos internos; sus dos etiquetas las afirma `test_compare.py`);
- el filtro "con un espacio" deja pasar un texto visible de una sola palabra (hoy no hay ninguno en estos modulos);
- algunas palabras de la lista existen sin tilde ("vengo", "paro", "jugo"): un texto futuro podria dar un falso positivo, que se arregla afinando la lista;
- fuera del diff: `Trends.jsx:321` "Ultimas {v.label}" y `Filters.jsx:11-13` "Ultimos N dias" (frontend). `Filters.jsx` ya lo cubre la 81. El de `Trends.jsx` hay que confirmarlo cuando la 81 se mergee.

Skills: no aplica (el Arquitecto ya dijo que no hay dominio nuevo)
OMC: plan=— · revisión=4 hallazgos LOW (0 arreglados) · verificación=—

## QA

## Pendiente

## Para el humano
