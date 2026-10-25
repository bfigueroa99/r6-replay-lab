from django.db import migrations, models

from replays.analytics.metrics import clutch_vs


def llenar(apps, schema_editor):
    """Calcula `clutch_vs` de lo ya importado con la misma regla del import.

    Corre en la base real al primer `runserver`: rondas sin jugadores o
    eventos sin nick no pueden tumbarla.
    """
    Round = apps.get_model("replays", "Round")
    RoundPlayer = apps.get_model("replays", "RoundPlayer")
    Event = apps.get_model("replays", "Event")

    cambiados = []
    for rnd in Round.objects.only("id").iterator(chunk_size=200):
        jugadores = list(RoundPlayer.objects.filter(round_id=rnd.id))
        if not jugadores:
            continue
        team_of = {p.username: p.team_index for p in jugadores}
        eventos = [
            {"kind": kind, "actor": actor, "target": target}
            for kind, actor, target in Event.objects.filter(round_id=rnd.id)
            .order_by("order")
            .values_list("kind", "actor_name", "target_name")
        ]
        valores = clutch_vs(eventos, team_of)
        for p in jugadores:
            vs = valores.get(p.username, 0)
            if vs and p.clutch_vs != vs:
                p.clutch_vs = vs
                cambiados.append(p)
        if len(cambiados) >= 200:
            RoundPlayer.objects.bulk_update(cambiados, ["clutch_vs"])
            cambiados = []
    if cambiados:
        RoundPlayer.objects.bulk_update(cambiados, ["clutch_vs"])


class Migration(migrations.Migration):

    dependencies = [
        ("replays", "0002_perfil_ubisoft"),
    ]

    operations = [
        migrations.AddField(
            model_name="roundplayer",
            name="clutch_vs",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(llenar, migrations.RunPython.noop),
    ]
