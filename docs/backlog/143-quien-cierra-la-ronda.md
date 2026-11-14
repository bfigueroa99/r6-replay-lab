# 143. Quien cierra la ronda

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K7
archivos: -
turnos: po 20261114T0040Z-chQsvnq

## PR

## Que gana quien usa la app

En las rondas que se cierran por eliminacion, cuantas veces la ultima baja
fue tuya cuando ganan, y cuantas fuiste la ultima victima de tu equipo
cuando pierden, por lado: separa al que remata del que abre, que es lo
unico que hoy mide Duelos de apertura.

## Criterios de aceptacion

- [ ] Agregado nuevo sobre tus rondas filtradas con
      `Round.win_condition == "KilledOpponents"`: en las ganadas, la ultima
      baja del feed (`Kill` de mayor `order`, sin teamkills) y si su autor
      eres tu (`closed`); en las perdidas, si la victima de esa ultima baja
      eres tu (`last_to_fall`). `rounds`, conteo y `pct` por lado y total.
      Test con una ronda ganada que cierras, una que cierra un compañero y
      una perdida en que caes ultimo.
- [ ] Las rondas ganadas por objetivo o tiempo (o con `win_condition`
      vacio) no entran. Test.
- [ ] Una ultima baja que es teamkill o muerte sin autor deja la ronda
      fuera del conteo de cierre, no la cuenta como tuya ni ajena. Test.
- [ ] Los filtros globales aplican sobre tu fila; test con filtro de lado.
- [ ] Se ve en Duelos o en el Resumen (el arquitecto elige) como tabla chica
      por lado con el `n` de rondas a la vista y aviso si es chico; sin dato,
      una nota. e2e con `seed_demo` y consola limpia. Fila nueva en
      `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador (otro tramo).
- Usarlo en el Rating.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
