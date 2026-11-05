from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def llenar(apps, schema_editor):
    """Marca las aperturas devueltas de lo ya importado copiando `Event.traded`.

    No recalcula trades: copia la marca que dejo `annotate_trades` con la
    ventana vigente al importar o al ultimo `recompute`, la misma que ya
    sostiene el `was_traded` que se muestra. Corre en la base real al primer
    `runserver`: rondas sin eventos o que abren con un Death no la tumban.
    """
    RoundPlayer = apps.get_model("replays", "RoundPlayer")
    Event = apps.get_model("replays", "Event")

    primer_kill = Event.objects.filter(round_id=OuterRef("round_id"), kind="Kill").order_by("order")
    candidatas = RoundPlayer.objects.filter(opening_kill=True).annotate(
        autor=Subquery(primer_kill.values("actor_name")[:1]),
        tradeada=Subquery(primer_kill.values("traded")[:1]),
    )
    ids = [
        pk
        for pk, username, autor, tradeada in candidatas.values_list(
            "pk", "username", "autor", "tradeada"
        )
        if tradeada and autor == username
    ]
    for inicio in range(0, len(ids), 500):
        RoundPlayer.objects.filter(pk__in=ids[inicio : inicio + 500]).update(
            opening_kill_traded=True
        )


class Migration(migrations.Migration):

    dependencies = [
        ("replays", "0003_roundplayer_clutch_vs"),
    ]

    operations = [
        migrations.AddField(
            model_name="roundplayer",
            name="opening_kill_traded",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(llenar, migrations.RunPython.noop),
    ]
