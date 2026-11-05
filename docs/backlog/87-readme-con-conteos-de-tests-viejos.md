# 87. El README dice que la suite tiene 419 tests y vitest 65

estado: revisado
candado: -
rama: claude/equipo-dev/87-readme-con-conteos-de-tests-viejos
tipo: bug
epica: -
area: docs
prioridad: 5
fuente: QA 20261105T1521Z-cGymdxX, deriva de docs sobre dev 85009f6 (fallback sin trabajo: 81, 86 y 84 tenian candado de otras sesiones)
archivos: README.md
turnos: qa 20261105T1521Z-cGymdxX, arquitecto 20261105T1547Z-cDskDBu, dev 20261105T1706Z-cYDJ3ec, revisor 20261105T1734Z-c34hH6Y

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

Arquitecto 20261105T1547Z-cDskDBu, sobre dev 0861b0b. Una sola forma obvia:
sin arena ni consenso.

`archivos:` solo `README.md` (y esta ficha). Ninguna rama abierta (79, 81,
84) toca `README.md`: no hay orden de merge que cuidar.

Cambios exactos, tres lineas y nada mas (en el arbol el texto sigue
arrancando en la misma columna que hoy):

1. `README.md:270`
   `| \`manage.py test tests\` | Corre la suite (419 tests). |`
   -> `| \`manage.py test tests\` | Corre la suite completa. |`
2. `README.md:430`
   `  tests/                419 tests (parser, metricas, agregados, coach, API)`
   -> `  tests/                tests (parser, metricas, agregados, coach, API)`
3. `README.md:431`
   `frontend/               React + Vite + recharts (65 tests con vitest)`
   -> `frontend/               React + Vite + recharts (tests con vitest)`

Orden: editar, `grep -nE "[0-9]+ tests" README.md` (vacio), `git diff --stat`
(1 archivo, 3+/3-), `check.sh`.

Tests: ninguno nuevo; es un README. Que puede romperse: nada que ejecute
codigo; el riesgo es tocar otra linea (lo cubren el criterio "Ninguna otra
linea cambia" y el diff de 3 lineas). Verificacion manual: el README
renderizado en GitHub, la tabla de comandos y el arbol sin desalinear.

Skills: no aplica (docs, ningun dominio nuevo).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261105T1706Z-cYDJ3ec, sobre dev 67c23f7 menos este commit; base origin/dev al reclamar.)

Las tres lineas del diseno, tal cual: `README.md:270` dice "Corre la suite
completa.", y `README.md:430`/`431` quedan "tests (parser, metricas,
agregados, coach, API)" y "(tests con vitest)" sin cambiar la columna del
arbol. Sin desvios.

- `grep -nE "[0-9]+ tests" README.md`: vacio (rc=1).
- `git diff --stat origin/dev...HEAD -- README.md`: 1 archivo, 3+/3-. CRLF
  intacto (el README esta en CRLF y las lineas editadas siguen en `\r\n`).
- `verificar.sh`: VERDE 67c23f7dc en 155s: 963 tests backend, 199 vitest,
  64 e2e. Todo en verde. (Ya no son 954/190/61 como en la repro: justo lo
  que esta ficha evita fijar en el README.)

Tests: ninguno nuevo (docs). Para el Revisor: el criterio "ninguna otra
linea cambia" se ve en `git diff origin/dev...HEAD -- README.md`.

Skills: no aplica (docs).
OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## Revision 2026-11-05 sobre adf6332

revisor 20261105T1734Z-c34hH6Y. Dev no se movio desde la implementacion: sin merge.

Revision a ciegas (`omc-code-reviewer`, eje de estandares; diff de 3 lineas
de docs, sin eje de intencion ni de seguridad): sin hallazgos. Tabla de
comandos con sus dos celdas, arbol con la misma columna, CRLF en las 469
lineas del README.

Criterios, confirmados por el lider:

- [x] `grep -nE "[0-9]+ tests" README.md`: vacio (rc=1).
- [x] Ninguna otra linea cambia: `git diff --stat origin/dev...HEAD -- . ':(exclude)docs/backlog'`
      = `README.md | 6 +++---`, 3+/3-, las tres lineas del diseno.
- [x] `verificar.sh`: VERDE f9964af78 en 100s: 963 tests backend, 199
      vitest, 64 e2e. Todo en verde.

Sin metricas nuevas, sin codigo, `archivos:` respetado.

Hallazgos: ninguno.

Veredicto: aprobar -> `revisado`.

Skills: no aplica (docs).
OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## QA

## Para el humano
