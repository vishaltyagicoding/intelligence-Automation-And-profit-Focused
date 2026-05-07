# Generated migration for signal_alerts app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SignalAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crypto', models.CharField(choices=[('BTCUSD', 'Bitcoin'), ('ETHUSD', 'Ethereum'), ('LTCUSD', 'Litecoin'), ('XRPUSD', 'Ripple')], max_length=10)),
                ('timeframe', models.CharField(choices=[('5m', '5 Minutes'), ('15m', '15 Minutes'), ('30m', '30 Minutes'), ('1h', '1 Hour'), ('2h', '2 Hours'), ('4h', '4 Hours'), ('1d', '1 Day')], max_length=5)),
                ('email', models.EmailField(max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signal_alerts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signal_alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='signalalert',
            constraint=models.UniqueConstraint(fields=('user', 'crypto', 'timeframe'), name='unique_user_crypto_timeframe'),
        ),
    ]
