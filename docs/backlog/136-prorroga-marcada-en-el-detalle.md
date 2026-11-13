# 136. La prorroga marcada en el detalle de la partida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F25 (la tira de Partidas, ficha 103, ya corta antes de la prorroga; el detalle no)
archivos: -
turnos: po 20261113T2157Z-cG2vDSe

## PR

## Que gana quien usa la app

En el detalle de una partida, las rondas de prorroga llevan una marca y un
separador antes de la primera, como ya hace la tira de rondas del listado de
Partidas: hoy en el detalle una ronda de prorroga se lee como una mas y no se
ve donde termino el tiempo reglamentario.

## Criterios de aceptacion

- [ ] `/api/matches/<id>/` devuelve en cada ronda `overtime` (`true` si
      `Round.overtime_number > 0`), la misma regla que la tira de
      `/api/matches/`. Test Django con una partida de 3 rondas normales y 2 de
      prorroga, y otro sin prorroga (todas `false`).
- [ ] En el detalle, la lista o pestañas de rondas muestran un separador
      (texto "Prórroga") antes de la primera ronda de prorroga y cada ronda de
      prorroga con una marca visible y nombre accesible que diga "prórroga".
      Logica pura en un helper con vitest (sin prorroga no hay separador; el
      separador va una sola vez).
- [ ] La tira o el selector de ronda siguen funcionando con teclado igual que
      antes (las flechas no se detienen en el separador). Test vitest o e2e.
- [ ] e2e: `seed_demo` no tiene prorroga; el e2e abre un detalle del seed y
      verifica que no aparece el separador y la consola queda limpia.

## Fuera de alcance

- Cambiar la tira de Partidas (ya lo hace).
- Metricas de prorroga nuevas (ficha 127, Tendencias).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
