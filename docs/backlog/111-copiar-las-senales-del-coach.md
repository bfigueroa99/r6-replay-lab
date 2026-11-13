# 111. Copiar las señales del Coach como texto

estado: entregado
candado: -
rama: claude/equipo-dev/111-copiar-las-senales-del-coach
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H6
archivos: frontend/src/textoCoach.js (nuevo), frontend/src/textoCoach.test.js (nuevo), frontend/src/pages/Coach.jsx (GROUPS y format se mudan; boton Copiar señales), frontend/e2e/humo.spec.js
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261113T0003Z-cVnayJ8, dev 20261113T1603Z-cHj1H4k, revisor 20261113T1647Z-cRa8Bqm, qa 20261113T1651Z-cxTme8t, release 20261113T1651Z-cxTme8t

## PR

Titulo: `[equipo-dev][frontend] Copiar las señales del Coach como texto`

### Que cambia

En Coach, el botón "Copiar señales" copia al portapapeles las señales que
ves (título, detalle, qué hacer, número, referencia y muestra) en texto
plano, agrupadas como en la página y con los filtros activos en la primera
línea, para pegarlas en el chat del equipo. Nada sale del PC. Sin señales no
hay botón; sin portapapeles, avisa en vez de romper.

### Por que esto y no otra cosa

Ficha 111 (ALCANCE.md H6, épica exportar). Exportar a archivo o imagen y
copiar las señales del Inicio quedaron fuera. Grupos y formato del número se
mudan a `textoCoach.js` para que lo copiado no se desalinee de la página.

### Como se probo

- `check.sh` (con `verificar.sh`): ver la última línea de la QA y el commit de entrega.
- Tests nuevos: `frontend/src/textoCoach.test.js` (11: sin señales `null`, sin y con filtros en orden, todos los filtros, dos señales en orden de grupo, referencia y muestra solo si existen, formato del número, umbral de decimales, sin espacios al final, orden de los grupos); e2e `el Coach copia sus señales` (sin filtros y con `?side=Defense`, consola limpia).
- Verificación manual (QA): Chromium claro y oscuro sobre `seed_demo`, texto copiado contra `/api/coach/` con 4 combinaciones de filtros, sin portapapeles y con `writeText` que rechaza, teclado, contrastes 6.51:1 y 6.45:1; base vacía sin botón.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=5 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=—
- OMC: plan=— · revisión=4 hallazgos (1 arreglado, test; 0 CRITICAL/HIGH) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: ninguna (modern-web-guidance y ux-copy no se leyeron: boton y aviso copian el patron y los textos de "Copiar resumen" de la partida, sin CSS nuevo).
- Skills del repo: accessibility-review (qa: 0 Critical/Major, contrastes 6.51 y 6.45), validate-data no aplica (sin numero nuevo), design-critique no aplica (boton en un panel existente).

### Riesgos y lo que no entra

Sin backend, migración ni dependencias. El caso sin portapapeles no tiene
test automático (probado a mano). El mapa sale por su slug y la sesión como
"Sesión N" contando desde la más reciente.

### Como probarlo en 2 minutos

```powershell
cd frontend; npx vitest run src/textoCoach.test.js; npm run build
cd ..\backend; python manage.py runserver
```

Abrir `/coach`, apretar "Copiar señales" y pegar: primera línea
`Coach · Sin filtros`, después los grupos. Con `?side=Defense`, la primera
línea dice `Coach · Filtros: Solo defensa`.

### Para el humano

Aviso, no frena: si preferís el nombre del mapa y la fecha de la sesión en el
texto copiado, es otra ficha chica.

### Candidatos descubiertos

Ninguno

## Que gana quien usa la app

Un boton en Coach copia al portapapeles las señales que se ven (titulo,
numero, muestra y consejo) en texto plano, con los filtros activos en la
primera linea, para pegarlas en el chat del equipo o mandarselas a quien te
entrena. Nada sale de la PC: es el portapapeles, como "Copiar resumen" de la
partida y de la sesion.

## Criterios de aceptacion

- [ ] Funcion pura nueva (p. ej. `frontend/src/textoCoach.js`) que arma el
      texto desde la respuesta de `/api/coach/` y los filtros: primera
      linea con los filtros activos (o "Sin filtros"), una linea o bloque por
      señal en el orden que se muestran, sin HTML. Vitest con dos señales,
      con y sin filtros.
- [ ] Sin señales, el boton no aparece (o queda deshabilitado con la razon
      en `title`). Vitest de la funcion con lista vacia.
- [ ] Sin `navigator.clipboard` (http que no es localhost) el boton avisa
      que no se pudo copiar en vez de romper, igual que el de la partida.
- [ ] e2e: en `/coach` con el seed, el boton copia y el texto copiado
      (leido con `page.evaluate` sobre `navigator.clipboard.readText` con
      el permiso de Chromium, como el e2e que ya prueba "Copiar resumen", o
      espiando `writeText`) contiene el titulo de una señal del seed;
      consola limpia.

## Fuera de alcance

- Exportar a archivo o imagen.
- Copiar las señales del Inicio (el mismo texto puede reusarse despues).
- Backend: `build_insights` ya devuelve todo.

## Diseno

(arquitecto 20261113T0003Z-cVnayJ8) Solo frontend, con el patron de "Copiar
resumen" de la partida: `textoCoach.js` (pura) con `GRUPOS_COACH` y
`formatoCoach` mudados de `Coach.jsx`, `lineaDeFiltros` en el orden de
`CLAVES_DE_URL` y `textoCoach`; boton en el `page-head` del Coach; vitest y
e2e `el Coach copia sus señales`. Detalle en `git log`.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1603Z-cHj1H4k) Diseno completo:

- `textoCoach.js`: `GRUPOS_COACH` y `formatoCoach` se mudan de
  `Coach.jsx` (que los importa); `lineaDeFiltros` (orden de
  `CLAVES_DE_URL`, "Sin filtros" si no hay) y `textoCoach` (`null` sin
  señales; grupos en el orden de la pagina; titulo, detalle, "Qué hacer" y
  la linea de numeros con las condiciones de `.meta`; sin espacios al final).
- `Coach.jsx`: boton "Copiar señales" en el `page-head` solo con señales,
  aviso "Copiado" / "No se pudo copiar: ..." como la partida; `useState`
  antes de los returns tempranos.
- `docs/metricas.md`: nada (no hay numero nuevo).

Desvios del diseno (revision ciega):
- MEDIUM corregido: mientras `/api/coach/` trae los filtros nuevos la
  pagina muestra las señales viejas, y copiar mezclaba la linea de filtros
  nueva con señales viejas: el boton queda `disabled` con `loading`.
- LOW corregido: el aviso "Copiado" se guarda junto al texto copiado y solo
  se ve mientras ese sea el texto actual (al cambiar filtros desaparece).
- LOW corregido: el vitest del modo compara contra `nombreDeModo('Bomb')`.
- LOW sin cambio (sigue el diseno): el mapa sale como el valor del filtro
  (slug, o `map_id` para una version) y la sesion como `Sesión N` (indice
  desde la mas reciente, cambia al importar una nueva). Va a `## Para el
  humano`.

Tests: vitest `textoCoach.test.js` (8; en rojo antes del modulo: "Failed to
load url ./textoCoach.js"). Mutaciones: `nombreDeModo(v)` -> `v` tumba
"nombra el resto de los filtros"; `!insights?.length` -> `!insights` tumba
"sin señales no hay texto". e2e `el Coach copia sus señales`: sin filtros
(`Coach · Sin filtros` y el titulo de `insights[0]` de la API) y con
`/coach?side=Defense` (`Coach · Filtros: Solo defensa`), consola limpia.
Criterios -> tests: funcion pura con y sin filtros (vitest); sin señales
(vitest `null`; el boton depende de eso); sin portapapeles (misma rama que
la partida, no forzable en Chromium, como dice el diseno); e2e.

Skills: no aplica (copiar al portapapeles ya resuelto dos veces en el repo).
Skills del repo: ninguna (modern-web-guidance y ux-copy no se leyeron: boton y aviso copian el patron y los textos de "Copiar resumen" de la partida, sin CSS nuevo).
OMC: plan=— · revisión=5 hallazgos (3 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre dd2cc0c

(revisor 20261113T1647Z-cRa8Bqm) Dos ejes de `omc-code-reviewer`: aprobar,
0 CRITICAL/HIGH. MEDIUM sin cambio (lo fijo el Diseno, va a `## Para el
humano`): el mapa sale como slug/`map_id` y la sesion como indice. LOW: sin
test automatico del caso sin portapapeles. Agregado por el Revisor: vitest
con filtros y dos señales. Veredicto: `revisado`.
OMC: plan=— · revisión=4 hallazgos (1 arreglado, test; 0 CRITICAL/HIGH) · verificación=—
Skills del repo: ninguna

## QA 2026-11-13 sobre 1d1eb81

(qa 20261113T1651Z-cxTme8t) Ejercitado el sistema. La rama trae `origin/dev` (e29393f, con la 115): merge sin conflictos, 030054e.

- `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --` -> `VERDE 030054e7e: 1181 tests backend, 353 vitest, 98 e2e`; tras los tests de borde de abajo, `VERDE 1d1eb81e4 en 192s: 1181 tests backend, 355 vitest, 98 e2e. Todo en verde.`
- Bases en el scratchpad (`SQLITE_PATH=<tmp>/x.sqlite3 manage.py migrate`): `seed_demo` (29 partidas, 203 rondas) en :8765 y vacia en :8766. `curl /api/coach/?<q>` con `''`, `side=Defense`, `map=bank`, `until=foo`, `page=-1`, `days=-1`, `map=nope`, `side=`, `session=0`, `gamemode=Bomb&ranked_only=1`: todos 200; `side=Defense&map=bank` da 0 señales con 30 rondas.
- Chromium (Playwright, script en el scratchpad), claro y oscuro, con permiso de portapapeles: `/coach` -> "Copiar señales" -> "Copiado"; el texto copiado empieza `Coach · Sin filtros`, trae `- <titulo>` de las 9 señales de la API, sin HTML ni espacios al final. `?side=Defense` -> `Coach · Filtros: Solo defensa` (7 de 7); `?map=bank&operator=Ash` -> `Coach · Filtros: Mapa: bank · Operador: Ash`; `?gamemode=Bomb&ranked_only=1&session=1` -> `Coach · Filtros: Sesión 2 · Modo: Bomba · Solo ranked`. Con otro filtro el aviso "Copiado" desaparece. Base vacia y `?side=Defense&map=bank` (0 señales): ningun boton. Consola limpia en todo.
- Sin portapapeles (`addInitScript` con `navigator.clipboard` indefinido) y con `writeText` que rechaza: "No se pudo copiar: el navegador no dio acceso al portapapeles.", consola limpia (criterio 3, a mano: no hay test automatico).
- `accessibility-review`: el boton es `button` con nombre "Copiar señales", se alcanza con Tab despues de "Importar replays" y Enter copia; contraste boton 6.51:1, aviso 6.45:1. 0 Critical, 0 Major.
- `vite build`: chunk inicial `index` 199.89 kB en dev -> 199.91 kB en la rama; `Coach` (lazy) 8.61 -> 10.46 kB.
- Mutacion en `textoCoach.js` (todo restaurado): `if (senal.sample)` -> `if (true)` cae "la referencia y la muestra van solo si existen"; orden de `CLAVES_DE_URL` invertido cae 2 tests. Sobrevivian sin `trimEnd`, umbral `< 10` -> `< 100` y sin `Math.abs`: **agregados por QA** (pasan) "de 10 para arriba el numero va sin decimales, aunque no sea entero" y "una señal sin detalle no deja espacios al final de la linea"; con ellos los tres caen.
- Fuera de la ficha (ya estaba): la señal de trades dice "El 92%" en el titulo y `untraded_death_pct: 93` en la linea de numeros (redondeo distinto en backend y `formatoCoach`); la pagina muestra lo mismo. Anotado en `ALCANCE.md`.
- Sin numero nuevo (validate-data no aplica), sin migracion, parser, Electron ni `.ps1`: nada para verificar en el PC.

Criterios: 1 a 4 cubiertos con la evidencia de arriba. Veredicto: `aprobado`.

Skills: no aplica.
Skills del repo: accessibility-review (qa: 0 Critical/Major, contrastes 6.51 y 6.45), validate-data no aplica (sin numero nuevo), design-critique no aplica (boton en un panel existente).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- Aviso, no frena (dev): el texto copiado nombra el mapa por el valor del
  filtro (`bank`, o el numero de version) y la sesion como `Sesión N`
  contando desde la mas reciente, como dijo el diseno. Si preferis el nombre
  del mapa y la fecha de la sesion, es otra ficha chica (necesita los datos de
  `/api/filters/` y `/api/sessions/`).
