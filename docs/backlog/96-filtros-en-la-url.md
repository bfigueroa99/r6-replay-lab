# 96. Filtros en la URL

estado: propuesto
candado: arquitecto 2026-11-06 02:05 UTC
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 3
fuente: A10 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05; la rama `claude/dazzling-einstein-w3qcyq` sigue y trae `frontend/src/filtros.js` como referencia, no para copiar a ciegas)
archivos: -
turnos: po 20261106T0041Z-cSxDY1g

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy los filtros globales viven en un `useState` de `App.jsx`: recargar la
pagina (o reabrir la app de escritorio) los pierde, y una vista filtrada
("Ranked, Oregon, ultimos 30 dias, en defensa") no se puede guardar como
marcador ni volver a ella con el boton Atras. Con esto los filtros viajan en
la query de la URL y sobreviven a todo eso.

## Criterios de aceptacion

- [ ] Una funcion pura (p. ej. `frontend/src/filtrosUrl.js`) convierte
      filtros en query y query en filtros, ida y vuelta sin perdida, con
      tests de vitest: claves vacias no se escriben, claves desconocidas de la
      URL se ignoran, y valores raros (`days=abc`) se descartan en vez de
      llegar a la API.
- [ ] Elegir un filtro en cualquier pagina con barra de filtros actualiza la
      query de la URL (`replace`, no una entrada de historial por cada
      cambio de select); recargar la pagina deja los mismos filtros elegidos
      y los mismos numeros.
- [ ] Cambiar de pagina desde el menu conserva los filtros (como hoy) y la
      URL de destino los lleva en su query.
- [ ] Abrir directo una URL con filtros (por ejemplo
      `/tendencias?side=Defense&days=30`) muestra la barra con esos valores y
      la API recibe esos parametros.
- [ ] El e2e elige un filtro, recarga la pagina y comprueba que el select
      sigue con el valor y que un numero visible coincide con el de antes de
      recargar, sin errores en la consola.

## Fuera de alcance

- Filtros propios de una pagina (los de Partidas de la ficha 78, la pestaña
  elegida, la ronda seleccionada del detalle): solo los filtros globales de
  `Filters.jsx`. Si el diseno ve que los de Partidas salen gratis, se
  anota como siguiente tramo, no se mete aca.
- Guardar vistas con nombre, o cualquier persistencia en el backend o en
  `localStorage`: la URL es el unico lugar.
- Cambios a la API: ya entiende todos esos parametros.

## Diseno

(Arquitecto)

## Implementacion

## Para el humano

(Nada por ahora.)
