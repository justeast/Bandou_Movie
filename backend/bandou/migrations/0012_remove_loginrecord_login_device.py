# Generated by Django 5.1.3 on 2025-05-16 18:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bandou", "0011_loginrecord"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="loginrecord",
            name="login_device",
        ),
    ]
