# 126. A qué operador cambias tras perder

estado: propuesto
candado: arquitecto 2026-11-13T18:34Z
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O13 (Fuera de alcance de la ficha 113)
archivos: -
turnos: po 20261113T1643Z-c4P1LiD

## PR

## Que gana quien usa la app

El panel "Repetir o cambiar tras perder" de Operadores (ficha 113) dice si
cambiar de operador despues de una ronda perdida te sirve; esto dice a cual:
por operador con el que perdiste y lado, a que operadores cambias en tu
siguiente ronda del mismo lado y que winrate tiene esa ronda con cada uno.
Responde "cuando pierdo con Ash, ¿me va mejor yendo a Thermite o a Sledge?".

## Criterios de aceptacion

- [ ] `/api/operators/after-result/` (o una clave nueva de la misma
      respuesta) devuelve filas `from_operator`, `side`, `to_operator`,
      `rounds`, `won`, `winrate` con los mismos pares que el caso
      `switch` de `after_loss` de la 113 (misma partida, mismo lado,
      sin hueco de numeracion, sin operador vacio). Test con rondas armadas:
      pierdes con Ash, cambias dos veces a Thermite (ganas una) y una a
      Sledge (pierdes) -> Ash->Thermite 2 rondas 50 %, Ash->Sledge 1 ronda 0 %.
- [ ] La suma de `rounds` de las filas de un lado es igual al `rounds` de
      `after_loss.switch` de ese lado con los mismos filtros. Test.
- [ ] Los filtros globales aplican como en la 113 (`operator` elige la
      primera ronda del par: con `?operator=Ash` solo salen filas desde
      Ash). Test.
- [ ] Se ve en Operadores debajo del panel de la 113, con el aviso de muestra
      de la pagina (se avisa, no se oculta); sin cambios tras perder, un
      texto y no un error. El e2e de humo pasa por Operadores con la consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` ("A qué operador cambias tras perder").

## Fuera de alcance

- Lo mismo tras ganar (la base de la 113 ya lo cubre en agregado).
- Recomendar a que operador cambiar: se muestran los numeros, no un consejo.
- El mismo corte para el spawn (S3).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
