# 117. Hotfix: el e2e de las lineas punteadas cae casi siempre

estado: implementado
candado: -
rama: claude/equipo-dev/117-hotfix-graficos-punteados
tipo: bug
epica: -
area: frontend
prioridad: 1
fuente: QA de la 113 (P4, dev rojo reproducido en checkout completo)
archivos: frontend/e2e/accesibilidad.spec.js
turnos: dev 20261113T0404Z-cnRfz4a (hotfix P4, desde release)

## PR

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

## Para el humano

(nada)
