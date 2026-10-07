# NN. Titulo del item

estado: propuesto
candado: -
rama: -
area: backend
prioridad: 3
fuente: -
archivos: -
turnos: po 20261008T0305Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Dos frases. Si es trabajo interno (tests, deuda), que riesgo baja.

## Criterios de aceptacion

- [ ] Cada casilla se puede convertir en un test o en un `curl`.
- [ ] Entre 3 y 6. Las marca QA con la evidencia en `## QA`.

## Fuera de alcance

Lo que no entra, para que nadie lo agregue "ya que estamos".

## Diseno

(Arquitecto) Archivos exactos y por que esos; tests nuevos con nombre en
espanol; orden de implementacion; que puede romperse (migracion, recompute,
build, instalador); verificacion manual; fila de `docs/metricas.md` si hay
numero nuevo. Si pisa archivos de otra rama abierta o agrega migracion
mientras otra ya la agrega: "Implementar despues de que #NN se mergee".

## Implementacion

(Dev) Que quedo, que no, desvios del diseno y por que.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

(Solo si alguien dejo trabajo a medias: que falta y donde se trabo.)

## Para el humano

(Cualquiera, solo si hace falta una decision suya.)
