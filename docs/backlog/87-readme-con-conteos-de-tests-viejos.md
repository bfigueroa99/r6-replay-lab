# 87. El README dice que la suite tiene 419 tests y vitest 65

estado: propuesto
candado: -
rama: -
tipo: bug
epica: -
area: docs
prioridad: 5
fuente: QA 20261105T1521Z-cGymdxX, deriva de docs sobre dev 85009f6 (fallback sin trabajo: 81, 86 y 84 tenian candado de otras sesiones)
archivos: README.md
turnos: qa 20261105T1521Z-cGymdxX

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Quien clona el repo y corre `manage.py test tests` ve 954 tests, no los 419
que promete el README, y no sabe si le falta algo. Sin conteos fijos el
README deja de envejecer con cada ficha.

## Repro

Sobre dev 85009f6:

```bash
grep -nE "[0-9]+ tests" README.md
# README.md:270:| `manage.py test tests` | Corre la suite (419 tests). |
# README.md:430:  tests/                419 tests (parser, metricas, agregados, coach, API)
# README.md:431:frontend/               React + Vite + recharts (65 tests con vitest)
git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --
# VERDE 85009f63b en 119s: 954 tests backend, 190 vitest, 61 e2e. Todo en verde.
```

## Criterios de aceptacion

- [ ] `grep -nE "[0-9]+ tests" README.md` no devuelve conteos de la suite
      (se sacan o se cambian por una descripcion sin numero: "Corre la suite",
      "tests (parser, metricas, agregados, coach, API)", "tests con vitest").
- [ ] Ninguna otra linea del README cambia.
- [ ] `check.sh` en verde.

## Fuera de alcance

`docs/roadmap.md` (historia, no se toca), los conteos del informe del equipo,
cualquier otro texto del README.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano
