# 86. Duelos dice "0 rondas con estos filtros" con un filtro que tiene rondas pero ningun duelo

estado: propuesto
candado: arquitecto 2026-11-05T14:29Z
rama: -
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: hallazgo MEDIUM del Revisor de la 85 (`Duelos.jsx:43`), reproducido por la QA 20261105T1358Z-cxcyM5F en la app real
archivos: frontend/src/pages/Duelos.jsx, frontend/src/components/ui.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T1358Z-cxcyM5F

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Duelos decide si esta "vacia" por la cantidad de duelos (bajas y muertes
contra rivales), no por rondas. Con un filtro que deja rondas donde no
mataste ni moriste (un mapa o un lado), la pagina dice "0 rondas con estos
filtros" mientras el Resumen con el mismo filtro muestra esas rondas: el
numero es falso. Con el arreglo dice que no hay duelos, no que no hay rondas.

## Repro (dev a9f8a28)

1. Base de prueba con `backend/tests/factories.py`: una partida en Club
   House con una ronda en la que mataste a un rival (`make_event`) y otra en
   Bank con una ronda sin bajas ni muertes
   (`make_round_player(r, kills=0, died=False)`).
2. `runserver`, Duelos, Mapa = Bank: "0 rondas con estos filtros".
3. Resumen con el mismo filtro: la ronda esta. `/api/overview/?map=bank`
   da `rounds: 1`; `/api/duels/?map=bank` da `duels: 0`.

## Criterios de aceptacion

- [ ] Con un filtro que deja rondas y 0 duelos, Duelos mantiene titulo y
      barra y dice "0 duelos con estos filtros" (o equivalente), nunca
      "0 rondas" (e2e o vitest).
- [ ] Con un filtro que deja 0 rondas sigue diciendo "0 rondas con estos
      filtros" (el e2e de la 85 sigue verde).
- [ ] Base vacia sin filtros: EmptyState igual que hoy.

## Fuera de alcance

- Cambiar como se cuentan los duelos o los textos del resto de las paginas.
- Que `/api/duels/` devuelva rondas si no hace falta: el arreglo puede ser
  solo de texto (`SinRondasFiltradas` acepta el subtitulo).

## Diseno

## Implementacion

## QA

## Para el humano
