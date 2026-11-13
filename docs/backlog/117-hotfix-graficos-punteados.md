# 117. Hotfix: el e2e de las lineas punteadas cae casi siempre

estado: entregado
candado: -
rama: claude/equipo-dev/117-hotfix-graficos-punteados
tipo: bug
epica: -
area: frontend
prioridad: 1
fuente: QA de la 113 (P4, dev rojo reproducido en checkout completo)
archivos: frontend/e2e/accesibilidad.spec.js
turnos: dev 20261113T0404Z-cnRfz4a (hotfix P4, desde release), revisor 20261113T0804Z-cJw5MQs, qa 20261113T1203Z-cWfR3tT, release 20261113T1203Z-cWfR3tT

## PR

Titulo: `[equipo-dev][tests] El e2e de las lineas punteadas espera a que termine la animacion`

### Que cambia

Nada visible en la app. `check.sh` estaba rojo en `dev` por
`e2e/accesibilidad.spec.js:235`, que caia casi siempre: leia el
`stroke-dasharray` de las lineas mientras recharts todavia animaba el trazo.
Las tres lecturas de `punteadas` pasan a `expect.poll`, con las mismas
expectativas. Destraba la puerta de merge de toda la cola (la 113 espera por esto).

### Por que esto y no otra cosa

Ficha 117, hotfix P4 abierto desde la QA de la 113. Descartado: apagar la
animacion de recharts en la app (cambia la UI por un test) y relajar las
expectativas (dejaria de probar que la linea del eje derecho va punteada).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 1119fa2, 1165 tests backend, 334 vitest, 95 e2e.
- `--repeat-each 12` del test: 12 passed (revisor y QA, en sesiones distintas); con el archivo de dev, 2 de 6 fallan.
- Mutacion: sin `strokeDasharray="4 3"` en `EvolucionChart.jsx` o en la linea Rating de `Trends.jsx`, el test cae.
- OMC: plan=— · revisión=— · verificación=— (implementacion)
- OMC: plan=— · revisión=0 hallazgos · verificación=— (revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)
- Skills del repo: ninguna.

### Riesgos y lo que no entra

Solo toca un e2e. `expect.poll` espera hasta 5 s; la animacion dura bastante menos.

### Como probarlo en 2 minutos

```
cd frontend && npm run build
npx playwright test e2e/accesibilidad.spec.js -g "eje derecho" --repeat-each 12 --trace off
```
Tiene que decir `12 passed`.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Nada visible: baja el riesgo de no poder integrar. `check.sh` esta rojo en
`origin/dev` (fcba457) por `e2e/accesibilidad.spec.js:235` y ninguna rama
pasa la condicion f de la puerta de merge (la 113, PR #111, espera por esto).

## Repro

```
git checkout origin/dev && cd frontend && npm run build
npx playwright test e2e/accesibilidad.spec.js:226 --repeat-each 8 --trace off
```
En este contenedor: 7 de 8 fallan (en la rama de la 113, 6 de 8; dos
`check.sh` completos seguidos en rojo con la maquina libre). Error:
`punteadas` sale `[false, false]` y se esperaba `[false, true]` en
"Evolución por partida" de Resumen.

## Criterios de aceptacion

- [ ] El test "los graficos dicen que es cada linea y cual se lee en el eje
      derecho" pasa 12 de 12 con `--repeat-each 12`.
- [ ] Sigue afirmando lo mismo: `[false, true]`, `[false, false, true]` y
      `[false, false, false, true]` (no se relaja ni se salta nada).
- [ ] `check.sh` completo en verde.

## Fuera de alcance

Cambiar la animacion de recharts en los graficos de la app.

## Implementacion

(dev 20261113T0404Z-cnRfz4a) Causa: mientras recharts anima el trazo de una
`Line`, su `stroke-dasharray` es el del dibujo progresivo
(`<hecho>px <resto>px`); el patron `4px, 3px` de la linea punteada recien
aparece al terminar la animacion. La leyenda ya estaba esperada con
`expect.poll`, pero las tres lecturas de `punteadas` eran una sola foto y
caian en medio de la animacion. Arreglo: las tres con
`await expect.poll(...)`, mismas expectativas. Evidencia: antes 1 de 8 en
`origin/dev`, despues 12 de 12 (`--repeat-each 12`, 38.5 s).

OMC: plan=— · revisión=— · verificación=—

## Revision 2026-11-13 sobre 60252c0

(revisor 20261113T0804Z-cJw5MQs) VERDE 60252c015. Revision a ciegas
(`omc-code-reviewer`): sin hallazgos; una linea solida de recharts 2.15.0
nunca anima como `4px, 3px`, asi que el poll no da por punteada una que no
lo es. 12 de 12 con el arreglo; 2 de 6 fallan con el archivo de dev.
Veredicto: aprobar -> `revisado`. Detalle en `git log`.

Skills: no aplica.
OMC: plan=— · revisión=0 hallazgos · verificación=—

## QA 2026-11-13 sobre 1119fa2

(qa 20261113T1203Z-cWfR3tT) Solo cambia un e2e: sin backend, migracion,
parser ni `frontend/src`, asi que no aplican runserver con curl,
accesibilidad, design-critique ni validate-data.

- check.sh: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE 1119fa2a8 en 172s: 1165 tests backend, 334 vitest, 95 e2e`.
- 12 de 12: `cd frontend && E2E_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell
  npx playwright test e2e/accesibilidad.spec.js -g "eje derecho" --repeat-each 12 --trace off --reporter=line`
  -> `12 passed (38.1s)`.
- Mutacion 1: sin `strokeDasharray="4 3"` en `src/components/EvolucionChart.jsx:61`,
  `npm run build` y el mismo test -> `1 failed` en la linea 237 (`[false, true]`).
- Mutacion 2: sin `strokeDasharray="4 3"` en `src/pages/Trends.jsx:441` (Rating)
  -> `1 failed` en la linea 241 (`[false, false, true]`). Restaurado y
  reconstruido; `git status` limpio. El poll no tapa una linea que deja de
  ser punteada: agota el tiempo y cae.
- Mismas expectativas que en dev, nada saltado: confirmado en el diff.

Veredicto: `aprobado`.

Skills del repo: ninguna (sin pantallas ni numeros nuevos).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
