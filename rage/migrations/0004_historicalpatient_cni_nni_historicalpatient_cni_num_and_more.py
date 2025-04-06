# Generated by Django 4.2.20 on 2025-04-05 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rage', '0003_historicalvaccination_lot_vaccination_lot'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalpatient',
            name='cni_nni',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalpatient',
            name='cni_num',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalpatient',
            name='num_cmu',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='cni_nni',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='cni_num',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='num_cmu',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
