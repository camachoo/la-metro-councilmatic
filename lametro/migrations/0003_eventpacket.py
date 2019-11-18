# Generated by Django 2.1.14 on 2019-11-13 22:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lametro', '0002_billpacket_eventagendaitem_eventrelatedentity_membership_relatedbill'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPacket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('url', models.URLField()),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='packet', to='lametro.LAMetroEvent')),
            ],
        ),
    ]