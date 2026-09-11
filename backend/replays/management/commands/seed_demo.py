"""Datos sinteticos para los tests end to end.

No es una demo para mostrarle a nadie: es el fixture del e2e, y por eso las
cifras estan elegidas a mano y no al azar. Las pruebas afirman numeros exactos
sobre este set (que sitio queda marcado como dormidero, cual como solido, cual
no alcanza a decir nada), asi que cambiar la tabla de abajo es cambiar el
contrato de esas pruebas.

Nunca escribe sobre una base que ya tiene partidas salvo que se lo pidan con
--force: el que corre esto en la maquina equivocada no deberia perder su
historial por una letra.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from replays.models import Event, Match, Player, Round, RoundPlayer

ME = "BearF99"
COMPANEROS = ("Chamo", "Seba", "Nico", "Pauli")
RIVALES = ("Thorn.exe", "Kaid_", "Mozzie99", "Wamai")

#: (mapa, sitio, rondas, rondas en que quedas fuera de posicion).
#:
#: Los dos extremos estan puestos para que el veredicto de la pagina de
#: posicionamiento pase la banda de ruido con holgura, y los cuatro del medio
#: para que no la pase ninguno: un e2e que solo ve casos claros no prueba que la
#: banda sirva para algo.
#: La ultima fila es a proposito diminuta: sin una zona flaca no hay como probar
#: que el corte por muestra minima sirva para algo, y un historial real siempre
#: tiene un sitio que jugaste cuatro veces.
PERFIL = (
    ("Club House", "B Church, B Arsenal Room", 40, 34),   # 85.0% -> dormidero
    ("Club House", "A Bedroom, A Gym", 30, 17),           # 56.7% -> ruido
    ("Border", "B Armory, B Archives", 35, 21),           # 60.0% -> ruido
    ("Border", "A Ventilation, A Workshop", 28, 7),       # 25.0% -> solido
    ("Bank", "B Lockers, B CCTV", 36, 20),                # 55.6% -> ruido
    ("Bank", "A Executive, A Archives", 30, 17),          # 56.7% -> ruido
    ("Bank", "A Vault, A Gold Partition", 4, 2),          # 4 rondas -> bajo el corte
)

SPAWNS = {
    "Club House": ("Warehouse", "Muddy Road"),
    "Border": ("Valley", "East Alley"),
    "Bank": ("Boulevard", "Park"),
}

OPERADORES = {"Attack": ("Zofia", "Ash", "Thermite"), "Defense": ("Mute", "Jager", "Rook")}

RONDAS_POR_PARTIDA = 7
INICIO = datetime(2026, 8, 1, 20, 0)


class Command(BaseCommand):
    help = "Carga un historial sintetico y deterministico para los tests e2e."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Borra lo que haya y vuelve a sembrar. Destructivo.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        if Match.objects.exists() and not opciones["force"]:
            raise CommandError(
                "La base ya tiene partidas. Corre esto contra una base vacia "
                "(SQLITE_PATH a un archivo temporal) o pasa --force si de "
                "verdad quieres borrarlas."
            )
        if opciones["force"]:
            Match.objects.all().delete()
            Player.objects.all().delete()

        yo = Player.objects.create(profile_id="pid-me", username=ME, is_me=True)
        companeros = [
            Player.objects.create(profile_id=f"pid-c{i}", username=n)
            for i, n in enumerate(COMPANEROS)
        ]
        rivales = [
            Player.objects.create(profile_id=f"pid-r{i}", username=n)
            for i, n in enumerate(RIVALES)
        ]

        rondas = self._plan()
        total = self._sembrar(yo, companeros, rivales, rondas)

        yo.first_seen = INICIO
        yo.last_seen = INICIO + timedelta(hours=len(rondas))
        yo.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Sembradas {Match.objects.count()} partidas y {total} rondas."
            )
        )

    def _plan(self) -> dict[str, list[dict]]:
        """Las rondas de cada mapa, por separado.

        Separadas y no en una lista plana porque despues se cortan en partidas:
        si el corte cruza de un mapa al siguiente queda una partida etiquetada
        con un mapa y rondas con sitios de otro, que es justo la clase de dato
        imposible que el e2e deberia detectar y no fabricar.
        """
        por_mapa: dict[str, list[dict]] = {}
        for mapa, sitio, cantidad, dormidas in PERFIL:
            for i in range(cantidad):
                por_mapa.setdefault(mapa, []).append({"site": sitio, "fuera": i < dormidas})
        return por_mapa

    def _sembrar(self, yo, companeros, rivales, plan) -> int:
        indice = 0
        numero = 0
        for mapa, rondas in plan.items():
            for inicio in range(0, len(rondas), RONDAS_POR_PARTIDA):
                tanda = rondas[inicio : inicio + RONDAS_POR_PARTIDA]
                ganadas = sum(1 for i in range(len(tanda)) if i % 2 == 0)
                match = Match.objects.create(
                    match_id=f"demo-{numero}",
                    folder=f"Match-demo-{numero}",
                    played_at=INICIO + timedelta(hours=numero * 3),
                    map_name=mapa,
                    map_slug=mapa.lower().replace(" ", "-"),
                    match_type="Ranked",
                    gamemode="Bomb",
                    rounds_count=len(tanda),
                    my_team_index=0,
                    my_score=ganadas,
                    opponent_score=len(tanda) - ganadas,
                    won=ganadas > len(tanda) - ganadas,
                )
                for n, datos in enumerate(tanda):
                    self._ronda(match, n, datos, mapa, indice, yo, companeros, rivales)
                    indice += 1
                numero += 1
        return indice

    def _ronda(self, match, n, datos, mapa, indice, yo, companeros, rivales) -> None:
        lado = "Attack" if n % 2 == 0 else "Defense"
        gane = n % 2 == 0
        fuera = datos["fuera"]
        rnd = Round.objects.create(
            match=match,
            number=n,
            site=datos["site"],
            my_side=lado,
            my_team_won=gane,
            win_condition="KilledOpponents",
            clock_start=180,
            clock_end=20,
            teams=[{"name": "YOUR TEAM", "mine": True}, {"name": "ENEMY TEAM", "mine": False}],
        )

        # quedar fuera de posicion es morir, sin bajas y sin que nadie te vengue
        bajas = 0 if fuera else (2 if indice % 5 == 0 else 1)
        murio = fuera or indice % 3 != 0
        tradeado = murio and not fuera and indice % 4 == 0
        muerte = 35.0 + (indice % 6) * 22

        RoundPlayer.objects.create(
            round=rnd, player=yo, username=ME, team_index=0, side=lado, is_me=True,
            won=gane, operator=OPERADORES[lado][indice % 3],
            spawn=SPAWNS[mapa][indice % 2] if lado == "Attack" else "",
            kills=bajas, died=murio, headshots=1 if bajas and indice % 3 == 0 else 0,
            one_vx=1 if (gane and not murio and indice % 17 == 0) else 0,
            opening_kill=bajas > 0 and indice % 6 == 0,
            opening_death=fuera and indice % 5 == 0,
            entry_kill=bajas > 0 and indice % 6 == 0,
            trade_kills=1 if (bajas > 1 and indice % 7 == 0) else 0,
            was_traded=tradeado,
            untraded_death=murio and not tradeado,
            death_clock=(180 - muerte) if murio else None,
            death_elapsed=muerte if murio else None,
            survived=not murio,
            kst=bool(bajas or not murio or tradeado),
        )

        for i, companero in enumerate(companeros[: 2 if indice % 2 else 3]):
            RoundPlayer.objects.create(
                round=rnd, player=companero, username=companero.username, team_index=0,
                side=lado, is_me=False, won=gane,
                operator=OPERADORES[lado][(indice + i) % 3],
                kills=(indice + i) % 2, died=(indice + i) % 3 != 0,
                survived=(indice + i) % 3 == 0,
                death_elapsed=60.0 + i * 15 if (indice + i) % 3 != 0 else None,
                kst=True,
            )

        lado_rival = "Defense" if lado == "Attack" else "Attack"
        for i, rival in enumerate(rivales[:3]):
            RoundPlayer.objects.create(
                round=rnd, player=rival, username=rival.username, team_index=1,
                side=lado_rival, is_me=False, won=not gane,
                operator=OPERADORES[lado_rival][(indice + i) % 3],
                kills=(indice + i) % 2, died=(indice + i) % 2 == 0,
                survived=(indice + i) % 2 != 0,
                death_elapsed=70.0 + i * 12 if (indice + i) % 2 == 0 else None,
                kst=True,
            )

        # el kill feed: sin el no hay duelos ni narrativa de la ronda
        orden = 0
        if murio:
            verdugo = rivales[indice % 3]
            Event.objects.create(
                round=rnd, order=orden, kind=Event.KILL, clock=180 - muerte,
                clock_raw=f"{int((180 - muerte) // 60)}:{int((180 - muerte) % 60):02d}",
                elapsed=muerte, actor=verdugo, actor_name=verdugo.username,
                target=yo, target_name=ME, headshot=indice % 4 == 0,
                operator=OPERADORES[lado_rival][indice % 3], traded=tradeado,
            )
            orden += 1
        for i in range(bajas):
            victima = rivales[(indice + i + 1) % 3]
            clock = 180 - (muerte - 12 - i * 8 if murio else 90 + i * 10)
            Event.objects.create(
                round=rnd, order=orden, kind=Event.KILL, clock=clock,
                clock_raw=f"{int(clock // 60)}:{int(clock % 60):02d}",
                elapsed=180 - clock, actor=yo, actor_name=ME,
                target=victima, target_name=victima.username,
                headshot=indice % 3 == 0, operator=OPERADORES[lado][indice % 3],
            )
            orden += 1
