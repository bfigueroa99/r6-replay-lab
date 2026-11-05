# 88. Textos que arma el backend (narrativa de la partida, coach) sin tildes

estado: entregado
candado: -
rama: claude/equipo-dev/88-textos-del-backend-sin-tildes
tipo: bug
epica: -
area: backend
prioridad: 4
fuente: QA 20261105T1521Z-cEexMKJ de la 81, recorriendo `/partidas/N` en Chromium con `seed_demo`. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". La 81 dejo fuera, a proposito, los textos que manda el backend
archivos: backend/replays/analytics/narrative.py, backend/replays/analytics/coach.py, backend/replays/analytics/aggregates.py, backend/tests/test_narrative.py, backend/tests/test_compare.py, backend/tests/test_textos_con_tildes.py
turnos: qa 20261105T1521Z-cEexMKJ, arquitecto 20261105T1547Z-cDskDBu, dev 20261105T1547Z-cLk3BF3, revisor 20261105T1613Z-czS2t8M, qa 20261105T1641Z-cpQZfWz, release 20261105T1641Z-cpQZfWz

## PR

Titulo: `[equipo-dev][backend] La narrativa de la partida, el Coach y la comparacion llevan tildes`

### Que cambia

La narrativa de cada ronda en el detalle de la partida ("te mató Thorn.exe. Nadie la vengó."), los consejos del Coach ("Antes que buscar más kills...") y las etiquetas de la comparacion de Tendencias ("Últimas 4 partidas", "Últimos 30 días") ahora llegan del backend con sus tildes, como el resto de la UI. Solo tildes: ni claves de señales, ni `metric`, ni el JSON cambian.

### Por que esto y no otra cosa

Ficha 88, encontrada por la QA de la 81 recorriendo `/partidas/N`: la 81 arreglo los textos del frontend y dejo fuera los que arma el backend. Descartado reescribir textos (fuera de alcance) y tocar los mensajes de error de la API (no los ve la UI).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 1fc5005, 963 tests backend, 199 vitest, 64 e2e.
- Tests nuevos (`tests/test_textos_con_tildes.py`): `test_los_textos_del_coach_y_la_narrativa_no_pierden_las_tildes` (guardia con `ast` sobre los literales de `coach.py` y `narrative.py`; sobre dev daba 57 hallazgos), `test_la_guardia_encuentra_una_palabra_sin_tilde` (la regex no esta rota) y `test_el_recorrido_encuentra_el_literal_y_salta_docstrings_y_claves` (el recorrido salta docstrings y claves como `fatiga-sesion`). `test_narrative.py` y `test_compare.py` al texto nuevo, sin borrar casos (18->18, 29->29).
- Verificacion manual: `seed_demo` + `runserver`, `curl` a las 29 partidas, Coach, Compare (con parametros borde) y Tendencias: 0 cadenas sin tilde; Chromium en `/partidas/1` y `/coach` sin errores de consola. Mutacion: quitar una tilde en cada uno de los tres modulos hace caer un test.
- OMC: plan=— · revisión=— · verificación=— (Diseno)
- OMC: plan=— · revisión=4 hallazgos LOW (0 arreglados) · verificación=— (Implementacion)
- OMC: plan=— · revisión=3 hallazgos LOW (1 cubierto con test) · verificación=— (Revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migraciones, `recompute` ni parser. Afuera a proposito: los textos de frontend que siguen sin tilde junto a la etiqueta del backend (`Trends.jsx:41-42` "7 dias"/"30 dias", `Trends.jsx:321` "Ultimas {label}", "sesion" en Tendencias, `Filters.jsx:11-13` "Ultimos N dias"), que son del alcance de la ficha 81 (`con hallazgos`). La guardia no mira `aggregates.py` (sus dos etiquetas las afirma `test_compare.py`) ni fragmentos de f-string sin espacio.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_textos_con_tildes tests.test_narrative tests.test_compare
python manage.py seed_demo; python manage.py runserver
```

Abrir `http://127.0.0.1:8000/partidas/1`: la narrativa de las rondas dice "te mató ... Nadie la vengó." y "La ronda se cerró por eliminación."; `/coach`: "buscar más kills", "el equipo jugó".

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno (lo del frontend ya esta en la 81).

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

Arquitecto 20261105T1547Z-cDskDBu, sobre dev 0861b0b: lista cerrada de literales a tildar en `narrative.py`, `coach.py` y las dos etiquetas de comparacion de `aggregates.py` (barrido con `ast`), mas una guardia `test_textos_con_tildes.py`. Identificadores, claves de señales, comentarios y docstrings sin tocar. Detalle completo en `git log` de la rama.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1547Z-cLk3BF3) Toda la lista del diseno, mas cuatro textos visibles que encontro el barrido (`quién abre, quién tradea`, `quedándote`, `ahí`, `funcionó`) y "Los {n} días anteriores". La guardia falla primero sobre dev (57 hallazgos) y pasa con el arreglo. Revision ciega: aprobar, 4 LOW dejados a proposito (anotados en Riesgos del PR).

OMC: plan=— · revisión=4 hallazgos LOW (0 arreglados) · verificación=—

## Revision 2026-11-05 sobre fe348bb

(revisor 20261105T1613Z-czS2t8M) Aprobar -> `revisado`. Hallazgo corregido: la guardia no probaba el recorrido con `ast`; lo cubre `test_el_recorrido_encuentra_el_literal_y_salta_docstrings_y_claves`. Los otros dos LOW, sin arreglo (f-string sin espacio; textos de frontend de la 81).

OMC: plan=— · revisión=3 hallazgos LOW (1 cubierto con test) · verificación=—

## QA 2026-11-05 sobre 1fc5005

(qa 20261105T1641Z-cpQZfWz; rama fusionada con dev 3d89622, sin conflictos)

- `verificar.sh`: VERDE 1fc5005 en 124 s (963 tests backend, 199 vitest, 64 e2e).
- Base vacia + `seed_demo`, `runserver`; `curl` a las 29 partidas, Coach, Compare y Tendencias con parametros borde (`until=foo`, `page=-1`, `n=-5`, `by=foo&n=abc`): todos 200, 0 cadenas sin tilde.
- Chromium (playwright) sobre `/partidas/1` y `/coach`: textos con tilde visibles, 0 errores de consola. En `/tendencias` queda "sesion", "7 dias" y "Ultimas {label}": son de `Trends.jsx` (frontend), alcance de la 81, no de esta.
- Mutacion: "Nadie la vengó" -> "vengo" en `narrative.py` hace caer `test_perder_el_primer_duelo_propio` y la guardia (`narrative.py:80 'vengo'`); "más kills" -> "mas" en `coach.py` hace caer la guardia (`coach.py:377 'mas'`); "Últimas" -> "Ultimas" en `aggregates.py` hace caer `test_compare` (failures=1). Restaurado, `git status` limpio.
- Sin migraciones, parser, `recompute`, Electron ni `.ps1`: no hay "Verificar en el PC". Sin cambios en `frontend/src`: el chunk no cambia.

Criterios: 1, 2 y 3 VERIFIED, 4 VERIFIED (verde de esta QA). Veredicto: `aprobado`.

Skills: no aplica
OMC: plan=— · revisión=— · verificación=PASS

## Pendiente

## Para el humano
