# 118. "Ver esas rondas" desde las señales del Coach

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F15 (salio del PR #14, cerrado sin merge el 2026-11-05; complementa la 112, que salta a una ronda puntual)
archivos: -
turnos: po 20261113T0404Z-cnRfz4a

## PR

## Que gana quien usa la app

Cada señal del Coach que habla de un mapa, un lado, un operador o un sitio
lleva un enlace "Ver esas rondas" que abre el Resumen ya filtrado por eso, y la
de un rival abre Duelos: de "Kafe es tu peor mapa" se pasa a los numeros de
Kafe en un clic, sin armar los filtros a mano.

## Criterios de aceptacion

- [ ] Cada señal de `build_insights` (`coach.py`) trae un campo `filters`
      (dict, vacio si la señal es general) con los filtros que la definen,
      en los mismos nombres que la API acepta (`map` como slug, `side`,
      `operator`, `site`); test: la señal `mapa-debil` trae `{"map":
      <slug>}` y una general trae `{}`.
- [ ] Los filtros globales que ya tenia la consulta del Coach (fechas, tipo,
      modo, sesion) se suman al enlace: abrir el enlace no pierde el periodo
      que estaba mirando. Vitest de la funcion pura que arma el `href`.
- [ ] En Coach, una señal con `filters` no vacio muestra el enlace "Ver esas
      rondas" a `/?<query>`; una de rival (`nemesis`, duelos por operador)
      enlaza a `/duelos?<query>`; una general no muestra enlace.
- [ ] e2e: desde `/coach` con `seed_demo`, el enlace de una señal de mapa
      abre el Resumen con el filtro de mapa puesto (selector y URL), consola
      limpia.

## Fuera de alcance

- Saltar a una ronda puntual (eso es la 112, `#ronda-N`).
- Señales nuevas o cambiar el texto de las que hay.
- Enlazar a una lista de rondas (no existe; es F1).

## Para el humano

(nada)
