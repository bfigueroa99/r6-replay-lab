# Plantilla del cuerpo del PR

Titulo: `[equipo-dev][area] Titulo corto en espanol` (area: `backend`,
`frontend`, `parser`, `tests`, `docs`, `infra`).

---

## Que cambia

Dos o tres frases: que ve o que gana quien usa la app. Si el cambio es
interno (tests, deuda), que riesgo baja.

## Por que esto y no otra cosa

De donde salio la tarea (ficha NN; bug encontrado en X; deuda anotada en
el item #N del roadmap) y que alternativas se descartaron en una linea cada una.

## Como se probo

- `./scripts/check.sh`: <n> tests backend, <n> tests frontend, build ok.
- Tests nuevos: lista con nombre y que caso cubre cada uno.
- Verificacion manual: que comando o URL, que se vio.

## Riesgos y lo que no entra

Migraciones, `recompute`, instalador, rendimiento con bases grandes. Y lo que
quedo afuera a proposito, con la ficha `propuesto` donde quedo anotado.

## Como probarlo en 2 minutos

Comandos exactos, en orden, y que tiene que verse. Si algo solo se puede
verificar en el PC (migraciones, recompute, parser, Electron, `.ps1`), va
aparte bajo "Verificar en el PC".

## Para el humano

Decisiones que necesitan su criterio, o `Nada`.

## Candidatos descubiertos

Fichas nuevas que quedaron en `propuesto` en la rama `backlog`, o `Ninguno`.
