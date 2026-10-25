# Replica en el equipo: paridad con la referencia

Como corre el pack Replica (`.claude/skills/replica-*`, MIT, de
https://github.com/Jakeschincariol/replica-skill) dentro del loop. Lo usa el
Investigador cuando le toca la familia 8 (ver su especificacion en
`roles/investigador.md`), y se lee de `$EQUIPO_REF` con `git show`, igual que el resto del
playbook. Las skills del pack llevan `disable-model-invocation: true`: eso
solo impide que el modelo las active por su cuenta con la herramienta Skill.
El rol las lee por su ruta y las sigue con las adaptaciones de este archivo,
que mandan sobre lo que digan ellas.

## Referencia

- **Apps:** r6-replay.com (https://r6-replay.com/) y Aurelix
  (https://aurelix.app/), las herramientas de replay que `docs/roadmap.md`
  ("Que hacen los competidores") llama la competencia real.
- **Tajada:** lo que un jugador de Siege mira de sus propias partidas: perfil,
  historial, detalle de una partida, desglose por operador, mapa y modo,
  comparacion con otros jugadores y progreso en el tiempo.
- **Para quien:** quien usa r6-replay-lab, un jugador que analiza sus replays
  en su PC.

Las dos parsean el mismo `.rec` que este proyecto, asi que casi toda su
matriz se puede comparar de igual a igual. Lo que muestren y el `.rec` no
entregue segun `docs/formato-rec.md` va como `skip` con el motivo, igual que
lo que venga de la API de Ubisoft. Los trackers de API (stats.cc, R6 Tracker)
quedaron fuera de la referencia el 2026-10-20, a pedido del humano: leen la
API de Ubisoft y no los replays, y la mayor parte de su matriz era `skip`.

**Como cambiarla.** Editar este bloque en un PR (desde la web de GitHub
alcanza) y mergearlo; toca `.claude/`, asi que lo mergea el humano. Cada
pasada compara la lista de apps de aca con la linea `Referencia:` de la
cabecera de `recon.md`: si no coinciden, rehace el recon entero con la
referencia nueva y la matriz nueva reemplaza a la vieja (la anterior queda en
el historial de git de la rama `backlog`).

## Donde queda cada cosa

Las skills escriben en `replica/`. En el equipo esa carpeta es
`docs/backlog/replica/` de la rama `claude/equipo-dev/backlog`: el
Investigador solo empuja ahi, esa rama solo admite `docs/backlog/`, y asi
queda versionado sin PR y a la vista desde la web. Nada va a `replica/` de la
raiz ni a `main`.

| archivo en `docs/backlog/replica/` | paso | que es |
|---|---|---|
| `recon.md` | recon | el mapa de la referencia (plantilla `recon-map.md` de replica-recon), con `Referencia:` y `Ultimo recon: AAAA-MM-DD` en la cabecera |
| `features.csv` | recon y cada pasada | la matriz de funciones |
| `parity.md` | paridad | salida de `parity.py --markdown` |
| `reviews.csv` | resenas | resenas reales, copiadas tal cual, con su link |
| `themes.json` | resenas | los temas de `reviews.py` adaptados al rubro |
| `feedback.md` | resenas | salida de `reviews.py` |
| `fixes.md` | resenas | las tres listas y el plan de arreglos |

Sin `screens/`, `clone-screens/` ni `diffs/`: el loop no guarda capturas de
la referencia (son su imagen, pesan en git y el aspecto no es lo que se
mide). Ningun archivo ni carpeta de ahi empieza con numero y guion:
`estado.sh` cuenta como ficha cualquier ruta de `docs/backlog/` con `/NN-`.

## Que entra al loop y que no

| skill | en el loop | por que |
|---|---|---|
| replica-recon | si | el mapa de la referencia y la matriz de funciones |
| replica-diff | si, solo `parity.py` | es la medida de paridad. `imgdiff.py` compara capturas de aspecto, y copiar el aspecto de la referencia no es objetivo |
| replica-entrepreneur | si, pasos 1 a 4 | lo que los usuarios de la referencia piden o sufren, con cita y link. El paso 5 (angulo de venta) no aplica: la app no se vende |
| replica-test | no | QA ya ejercita cada ficha (`check.sh` con el e2e de `frontend/e2e/`, `runserver`, `curl`, mutacion) y anota en la ficha. replica-test escribe otro `e2e/` y otro `bugs.md` con los flujos de la referencia y pide `@axe-core/playwright`, una dependencia nueva que `CLAUDE.md` no deja sumar: duplicaria a QA |
| replica-design | no | reconstruye el sistema de diseno de la referencia para parecerse a ella; la app tiene su propia interfaz |
| replica-architect, replica-build, replica-backend | no | son para reconstruir una app desde cero. Aca el trabajo entra por fichas, lo disena el Arquitecto y lo implementa el Dev |
| replica-brand, replica-launch | no | nombre, marca, precio y lanzamiento son decisiones del humano |
| replica-deploy | no | es produccion: exige el visto bueno del humano, y el repo publica con `scripts/release.ps1` |

Las que no entran se pueden correr a mano con `/replica-<nombre>` en una
sesion que el humano inicie.

## Cadencia

Es la familia 8 del Investigador y no rota como las demas: va primero en el
primer turno del Investigador en que su fila de la tabla de Fuentes de
`INVESTIGACION.md` lleve 7 dias o mas sin visita, o no exista. La regla de no
repetir una familia en turnos seguidos no la frena. El Investigador corre por
reloj cada 2 dias (franja 7 de los dias pares, 21:01 UTC) y cuando
`ALCANCE.md` tiene menos de 10 ideas libres, siempre que el pipeline no pida
otro rol antes (`turno.sh`): en la practica, una pasada por semana.

Dentro de cada pasada:

- **Siempre:** la columna `clone` contra `origin/main` y `parity.py`. No usan
  red: sin red se hacen igual.
- **Recon completo:** la primera vez (no hay `features.csv`), si cambio la
  referencia, o si `Ultimo recon:` tiene 28 dias o mas. Entre medio, solo el
  changelog, el blog y la ayuda de la referencia, para sumar filas nuevas.
- **Resenas:** solo las nuevas desde la ultima pasada.

La primera pasada puede ocupar el turno entero; ese turno no visita otras
familias.

## La pasada, paso a paso

Las herramientas del pack pueden no estar en el arbol de la rama `backlog`
(sale de un `main` viejo), asi que se sacan de `$EQUIPO_REF` a una carpeta
dentro de `.git`, que nunca se commitea:

```bash
source "$(git rev-parse --git-dir)/equipo-dev.env"
R="$(git rev-parse --git-dir)/replica-pack"; rm -rf "$R"; mkdir -p "$R"
git archive "$EQUIPO_REF" .claude/skills | tar -x -C "$R"
ls "$R/.claude/skills"     # replica-recon, replica-diff, replica-entrepreneur...
```

Las variables no sobreviven entre comandos: cada comando que use `$R` lo
vuelve a definir. Las skills se leen enteras antes de empezar:
`git show "$EQUIPO_REF:.claude/skills/replica-recon/SKILL.md"` y lo mismo con
`replica-diff` y `replica-entrepreneur`.

1. **Recon** (`replica-recon`, cuando toca). Lo que cambia respecto de la
   skill:
   - El paso 1 (alcance) no se pregunta: es el bloque Referencia.
   - Fuentes: solo paginas publicas que respondan a una lectura normal. Un
     403 de Cloudflare se anota en la tabla de fuentes de `recon.md` y se
     sigue: no se reintenta con otro cliente, otras cabeceras ni un mirror
     (`CLAUDE.md`). Alternativas publicas: centro de ayuda y FAQ, blog y
     changelog, fichas de tienda (App Store, Google Play, Overwolf), videos,
     articulos, prensa y Reddit si abre. Nunca una cuenta, tampoco la del
     humano: no hay nadie para manejarla.
   - Sin capturas: nada de `screens/`.
   - La matriz (paso 7) lleva dos columnas mas al final, que `parity.py`
     ignora: `feature,area,priority,original,clone,notes,referencia,evidencia`.
     `referencia` es `r6replay`, `aurelix` o `ambas`; `evidencia` es una URL
     que el turno abrio. Sin URL abierta, la fila no entra. `priority` dice
     cuanto pesa la funcion en la referencia (`must`: por lo que la gente la
     usa), no cuanto le costaria a la app.
   - `clone` es el estado de r6-replay-lab en `origin/main`: `yes`,
     `partial` (en `notes`, lo que falta), `no` o `skip`.
   - El paso 8 es `skip` con el motivo y la regla que lo manda, nunca `no`:
     lo que el `.rec` no entrega (`docs/formato-rec.md` y "Lo que el formato
     .rec NO entrega" de `CLAUDE.md`: coordenadas, armas, dano, precision,
     asistencias y score atribuibles, plants y defuses en temporadas nuevas);
     lo que vive en la API de Ubisoft (MMR, rango, historial de temporada,
     leaderboards, jugadores fuera de tus replays), salvo lo que el panel
     opcional de Ubisoft del perfil ya muestra, que es `yes`; y los no-goals
     (overlay in-game y todo lo que corre sobre el juego, cuentas, nube,
     telemetria). Un `no` es algo que la app podria hacer con lo que ya tiene
     y no hace.
   - El paso 9 (tamano) y el siguiente paso que propone (`/replica-architect`)
     no aplican.
2. **Paridad** (`replica-diff`, paso 1, en cada pasada). Recorrer las filas
   que no son `skip` contra `origin/main` (pantallas, rutas `/api/`,
   `docs/metricas.md`) y actualizar `clone`. Despues:

   ```bash
   R="$(git rev-parse --git-dir)/replica-pack"
   python3 -I "$R/.claude/skills/replica-diff/parity.py" docs/backlog/replica/features.csv
   python3 -I "$R/.claude/skills/replica-diff/parity.py" docs/backlog/replica/features.csv --markdown > docs/backlog/replica/parity.md
   ```

   El "Not shippable yet" de su salida no dice nada aca: la app no se lanza
   contra la referencia. Lo que importa es el puntaje y cuantos `must`
   faltan.
3. **Resenas** (`replica-entrepreneur`, pasos 1 a 4). Resenas y quejas
   publicas reales de la referencia: App Store y Google Play (tambien el feed
   RSS oficial de Apple), Overwolf, Trustpilot, Hacker News (API de Algolia),
   Reddit si abre, foros y el tablero de pedidos de la propia app si es
   publico. Cada fila de `reviews.csv` lleva el texto copiado tal cual y su
   URL. Nunca se inventa, se parafrasea ni se completa una resena; si hay
   14, son 14. La primera vez, `themes.json` de la skill se copia a
   `docs/backlog/replica/themes.json` y se le suman palabras del rubro (rank,
   MMR, wrong stats, ads, overlay, match history, operator).

   ```bash
   R="$(git rev-parse --git-dir)/replica-pack"
   python3 -I "$R/.claude/skills/replica-entrepreneur/reviews.py" docs/backlog/replica/reviews.csv \
       --themes docs/backlog/replica/themes.json --today "$(date -u +%F)" --out docs/backlog/replica/feedback.md
   ```

   `fixes.md` lleva las tres listas y el plan del paso 4. Cada arreglo del
   plan entra a `features.csv` con `original` en `no` (la referencia no lo
   tiene; `parity.py` lo lista aparte y no lo puntua). Un tema marcado
   `thin` se lista como thin y no se vuelve idea por si solo. El paso 5 y lo
   de precio y facturacion no aplican.
4. **A `ALCANCE.md`.** Cada `must` con `clone` en `no` o `partial`, y cada
   arreglo de `fixes.md` con evidencia que no sea thin, pasa los tres filtros
   del Investigador (dato, reglas duras, duplicado) y entra como idea a la
   epica `paridad-referencia` (se crea la primera vez). En la celda de la
   idea va `[fuente](url)` de la referencia, o la cita con su link; en datos,
   el campo de `pydissect/` o `models.py` que la alimenta. Un `must` que no
   pasa el filtro de dato no era `no`: vuelve a la matriz como `skip` con su
   motivo. Ahi termina: priorizar y escribir fichas es del PO, y nada de esto
   toca `docs/roadmap.md`, que quedo como historia.
5. **Registro.** La fila `8. Paridad con la referencia (Replica)` de la tabla
   de Fuentes de `INVESTIGACION.md` (ultima visita y senal) y, en la entrada
   del turno, una linea `Paridad: <n> / 100, must <hechos> de <total>, skip
   <n>, resenas <n> de <n> fuentes`. Commit `Investiga: 8, ...` en `backlog`,
   con la receta unica de push rechazado.
