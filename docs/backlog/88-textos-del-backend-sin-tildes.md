# 88. Textos que arma el backend (narrativa de la partida, coach) sin tildes

estado: propuesto
candado: arquitecto 2026-11-05 15:48 UTC
rama: -
tipo: bug
epica: -
area: backend
prioridad: 4
fuente: QA 20261105T1521Z-cEexMKJ de la 81, recorriendo `/partidas/N` en Chromium con `seed_demo`. `CLAUDE.md` (Estilo): "Los textos que ve el usuario en la UI si llevan tildes y ñ". La 81 dejo fuera, a proposito, los textos que manda el backend
archivos: backend/replays/analytics/narrative.py, backend/replays/analytics/coach.py, backend/tests/test_narrative.py, backend/tests/test_teamkills.py
turnos: qa 20261105T1521Z-cEexMKJ

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La narrativa de cada ronda en el detalle de la partida ("A los 35s perdiste
el primer duelo: te mató Thorn.exe. Nadie la vengó.") y los consejos del
Coach se leen con sus tildes, igual que el resto de la app despues de la 81.

## Repro

Sobre dev 0861b0b:

```bash
grep -nE '"[^"]*\b(despues|mas|tambien|segun|numero|dia|sesion|perdio|gano|mato|murio|abrio|arranco|vengo)\b[^"]*"' backend/replays/analytics/coach.py backend/replays/analytics/narrative.py
```

Da ~21 lineas de cadenas visibles, entre ellas `narrative.py:64`
"te mato {asesino}", `:66` "tu equipo perdio el primer duelo ... mato a",
`:68` "abrio la ronda", `:60` "Murio {victima}" / "arranco con uno menos",
`:80` "Nadie la vengo", `:91` "la vengo ... despues", y `coach.py:212`
"sal a roamear despues". En la app: `manage.py seed_demo`, `runserver`,
`/partidas/1`: "te mato Thorn.exe. Nadie la vengo."

## Criterios de aceptacion

- [ ] Las cadenas visibles de `narrative.py` llevan tildes ("mató", "murió", "perdió", "abrió", "arrancó", "vengó", "después").
- [ ] Un barrido de las cadenas visibles de `coach.py` (titulos, consejos, textos de señales) no deja otras sin tilde; identificadores, claves (`key`/`id` de señales), comentarios y docstrings siguen sin tildes.
- [ ] `test_narrative.py`, `test_teamkills.py` y cualquier e2e que afirme estos textos se actualizan al texto nuevo, sin borrar ningun caso.
- [ ] `check.sh` en verde.

## Fuera de alcance

Reescribir textos (solo tildes); cambiar claves de señales o del JSON;
mensajes de error de la API y de los comandos de `manage.py` (no los ve la UI
salvo el de importacion, que se puede sumar si el barrido lo encuentra).

## Diseno

## Implementacion

## QA

## Pendiente

## Para el humano
