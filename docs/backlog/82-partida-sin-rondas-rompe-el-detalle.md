# 82. Una partida sin rondas rompe el detalle de partida

estado: entregado
candado: -
rama: claude/equipo-dev/82-partida-sin-rondas-rompe-el-detalle
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: QA 20261105T0256Z-cFRtPBc de la ficha 75 (anotado alli como "ficha 81"; el 81 lo tomo otra sesion a la vez). En dev 7a87ddc, `frontend/src/pages/MatchDetail.jsx:33`: `const round = rounds[Math.min(selected, rounds.length - 1)]` da `rounds[-1]` = `undefined` con 0 rondas, y `round.label` (`:124`) tira `TypeError`
archivos: frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, frontend/e2e/partida-sin-rondas.json, backend/tests/test_partida_sin_rondas.py
turnos: qa 20261105T0256Z-cFRtPBc, arquitecto 20261105T1303Z-cfek47z, dev 20261105T1330Z-c4QLGh8, revisor 20261105T1358Z-caeHwMj, qa 20261105T1358Z-cxcyM5F, release 20261105T1358Z-cxcyM5F

## PR

Titulo: `[equipo-dev][frontend] Una partida sin rondas ya no deja el detalle en blanco`

### Que cambia

Una partida importada sin rondas (un `.rec` cortado o una carpeta a medias)
dejaba el detalle en blanco con un `TypeError` en consola. Ahora se ve la
cabecera, los KPIs, la matriz, los trades y el scoreboard, y el panel
Rondas dice "Esta partida no tiene rondas importadas.". Una partida con
rondas se ve igual que antes.

### Por que esto y no otra cosa

Ficha 82, bug encontrado por la QA de la 75. El backend ya respondia 200
con `rounds: []`: el arreglo es una guarda de render en `MatchDetail.jsx`.
Descartado: impedir que el import guarde partidas sin rondas (otra
decision, fuera de alcance).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre la rama fusionada con dev, 954 tests backend, 190 vitest, 61 e2e.
- Tests nuevos: `test_el_detalle_de_una_partida_sin_rondas_responde_200`
  (200, `rounds: []` y cuerpo igual a `frontend/e2e/partida-sin-rondas.json`,
  asi el e2e no prueba una forma vieja); e2e `una partida sin rondas muestra
  su cabecera y un aviso` (ruta interceptada; rojo sin el arreglo).
- Manual (QA): partida sin rondas creada con `factories.py`, `/partidas/<id>`
  con cabecera, aviso, paneles y "Copiar resumen"; consola limpia. 3
  mutaciones, las 3 caen. Chunk inicial igual.
- OMC: plan=— · revisión=— · verificación=—
- OMC: plan=— · revisión=1 hallazgo LOW (1 arreglado: comentario del e2e decia "lo genera") · verificación=—
- OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 4 criterios VERIFIED, 0 bloqueantes)

### Riesgos y lo que no entra

Sin migraciones ni cambios del backend de produccion. Si el detalle cambia
de forma, `test_partida_sin_rondas` obliga a regenerar el JSON del e2e. El
404 HTML de `/api/matches/<id inexistente>/` es la ficha 84.

### Como probarlo en 2 minutos

1. `cd backend; python manage.py shell -c "from tests.factories import make_match; print(make_match(map_name='Oregon', index=99, my_score=0, opponent_score=0).pk)"` (en una base de prueba).
2. `python manage.py runserver` y abrir `/partidas/<ese id>`.
3. Se ve "Oregon · 0-0" y el aviso "Esta partida no tiene rondas importadas.", sin errores en la consola.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Diseno

Arquitecto 20261105T1303Z-cfek47z: `round` en `null` sin rondas y panel
alternativo con el aviso; JSON compartido entre el e2e y un test de backend
que lo ata a la respuesta real (patron de `casosApertura.json`).

## Implementacion

Dev 20261105T1330Z-c4QLGh8: el diseno sin desvios. `.round-tab` se cuenta
dentro del panel Rondas porque la matriz de duelos usa la misma clase.

## Revision 2026-11-05 sobre 6494edd

Revisor 20261105T1358Z-caeHwMj: aprobar -> `revisado`. Test rojo antes del
arreglo reproducido; cuatro criterios cubiertos. Un LOW de estilo sin
arreglo (comentario largo en `humo.spec.js:8-9`).

## QA 2026-11-05 sobre b7e2cbe

QA 20261105T1358Z-cxcyM5F: `aprobado`. Rama fusionada con dev a9f8a28.
Criterios con evidencia en la app real, 3 mutaciones que caen,
omc-verifier PASS. Detalle en el commit `Prueba: 82` de la rama.

## Para el humano
