# 103. Tira de rondas en el listado de partidas

estado: entregado
candado: -
rama: claude/equipo-dev/103-tira-de-rondas-en-partidas
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F4 (el PR #14, que tocaba Matches.jsx, se cerro sin merge el 2026-11-05)
archivos: backend/replays/views.py (match_list), backend/tests/test_tira_de_rondas.py, frontend/src/tiraRondas.js, frontend/src/tiraRondas.test.js, frontend/src/pages/Matches.jsx, frontend/src/styles.css, frontend/e2e/tira-rondas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh, dev 20261106T0648Z-cYjqMjZ, dev 20261109T0345Z-c8x1kCc, revisor 20261109T1205Z-cP2rEUw, qa 20261109T1604Z-cyu4hFR, release 20261109T1604Z-cyu4hFR

## PR

Titulo: `[equipo-dev][fullstack] Tira de rondas en el listado de partidas`

### Que cambia

En Partidas, cada fila muestra la secuencia de rondas (columna "Secuencia"):
un cuadradito por ronda, verde ganada, rojo perdida, gris sin ganador claro,
con la letra del lado (A/D/?) y un corte antes de la prórroga. Las remontadas
y la mitad que se cayó se ven sin abrir la partida. El CSV exporta la
secuencia como texto (`G P - G | G G`).

### Por que esto y no otra cosa

Ficha 103 (ALCANCE F4, idea del PR #14 cerrado). La tira sale de `Round` en
una sola consulta por pagina y es de la partida entera: los filtros eligen
partidas, no recortan sus rondas. Clic a la ronda (F6), Inicio y Sesiones
quedan afuera.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre el commit de entrega (1100 tests backend, 295 vitest, 84 e2e).
- Tests nuevos: `test_tira_de_rondas.py` (8: orden, `won=null`, prorroga, sin rondas, filtros que no recortan, una consulta por pagina, tira por partida, lado vacio); `tiraRondas.test.js` (7); e2e `tira-rondas.spec.js` (celdas contra `strip`, CSV legible, consola limpia).
- QA: base sintetica con prorroga, ronda sin ganador y lado desconocido; `curl` con bordes y Chromium sobre `/partidas`; 4 mutantes caen.
- OMC: plan=— · revisión=— · verificación=— (diseno)
- OMC: plan=— · revisión=1 hallazgo (1 arreglado; sin subagente, la hizo el Dev) · verificación=— (implementacion)
- OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados, no bloquean) · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 4 criterios VERIFIED) (QA)

### Riesgos y lo que no entra

Sin migracion ni `recompute`. Peso: ~9 objetos chicos por fila; el chunk
inicial no crece (Matches lazy +1 KB). Fuera: clic a la ronda (F6), tira en
Inicio o Sesiones, bajas por ronda.

### Como probarlo en 2 minutos

```
cd backend; python manage.py runserver
```

Abrir `/partidas`: cada fila con rondas tiene la columna Secuencia; pasar el
mouse por un cuadradito muestra `R1 · ataque · ganada`. "Descargar CSV": la
columna Secuencia se lee como `G P G | G`.

Verificar en el PC: una partida con prorroga y una ronda sin ganador claro
(ficha 38) se ven distintas en Partidas; abrir el CSV en Excel.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Criterios de aceptacion

- [x] `strip` por fila de `/api/matches/` (`won`, `side`, `overtime`), una sola consulta por pagina.
- [x] La tira es de la partida entera: `side`, `site` y `operator` no la recortan.
- [x] `Matches.jsx` dibuja la tira (ganada, perdida, gris, lado, corte de prorroga, `title`); partida sin rondas sin tira y sin error.
- [x] Filtros y paginacion siguen igual; e2e ve la tira con la consola limpia.

## Diseno e implementacion

Arquitecto cFqJHEh, Dev c8x1kCc (136fc61, 71655cf). Desvios: ronda sin
ganador en el CSV como `-`; letra de la celda en `var(--bg)` por contraste.
Detalle en `git log` de la rama.

## Revision

Revisor cP2rEUw sobre c25627e, ciega en dos ejes: aprobar. Dos LOW no
bloqueantes: el CSV de Secuencia es lo que pidio el diseno; el e2e no
afirma la celda gris ni el corte (los cubre vitest, y la QA los vio en
Chromium).

## QA

QA cyu4hFR sobre 32988db: aprobar. `verificar.sh` VERDE; base vacia y
sembrada (prorroga, `won=null`, lado `""`, rondas desordenadas, partida sin
rondas); `curl` con `side`, `site`, `operator`, `until=foo`, `page=-1`,
`offset=-1`, `limit=99999`, `result=` -> 200 y tiras completas; Chromium:
7 celdas `win loss nula win loss win win`, letras `A A A D ? D A`, un corte,
consola limpia; chunk inicial igual que dev. Mutantes que caen: `overtime
>= 0`, tira filtrada por `side`, `won=null` como `loss`, corte en cada ronda
de prorroga. Detalle completo en el commit `Prueba: 103`.

## Para el humano

(nada)
