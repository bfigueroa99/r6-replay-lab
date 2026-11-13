# 129. Filtro de operador en la pagina Operadores

estado: propuesto
candado: arquitecto 2026-11-13T19:31Z
rama: -
tipo: funcionalidad
epica: operadores
area: frontend
prioridad: 3
fuente: ALCANCE.md O14 (friccion que vio la QA de la 113)
archivos: -
turnos: po 20261113T1858Z-cxdASk3

## PR

## Que gana quien usa la app

Operadores monta `Filters` con `showOperator={false}`, asi que los paneles
que si usan `operator` (Repetir o cambiar tras perder, A qué operador
cambias, Por sitio) solo lo reciben por la URL o heredado de otra pagina. Un
selector propio deja usar ese filtro sin editar la URL.

## Criterios de aceptacion

- [ ] Operadores muestra el selector de operador de `Filters`; elegir uno
      pone `?operator=<nombre>` en la URL y los paneles que leen `operator`
      recargan con el. e2e: elegir un operador del seed y ver la URL y la
      tabla Repetir o cambiar con solo filas de ese operador (numeros de la API).
- [ ] Las tablas por operador de la pagina (Todos y los grupos por lado) no
      se vacian con el filtro: la fila del operador elegido queda resaltada
      (clase y `aria-current` o equivalente) y las demas siguen. vitest o e2e.
- [ ] Quitar el filtro (opcion "Todos") vuelve a la vista sin resaltado y
      saca `operator` de la URL. e2e.
- [ ] La vista "sin rondas filtradas" de Operadores tambien muestra el
      selector, para poder quitar un operador que deja la pagina vacia. e2e.
- [ ] Consola limpia en todo el recorrido; sin cambios de backend (los
      endpoints ya aceptan `operator`).

## Fuera de alcance

- Selector de varios operadores a la vez.
- Cambiar como filtran `operator` los endpoints.
- El mismo resaltado en otras paginas.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
