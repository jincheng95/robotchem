# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-23 00:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0002_run_calorimeter'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('measured_at', models.DateTimeField(verbose_name='Measured At')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='Received At')),
                ('temp_ref', models.FloatField(verbose_name='Reference Temp (Celsius)')),
                ('temp_sample', models.FloatField(verbose_name='Sample Temp (Celsius)')),
                ('heat_ref', models.FloatField(verbose_name='Reference Heat Flow Since Last Measurement (Joules)')),
                ('heat_sample', models.FloatField(verbose_name='Sample Heat Flow Since Last Measurement (Joules)')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='controls.Run', verbose_name='Run')),
            ],
        ),
    ]