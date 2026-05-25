# Generated migration for adding status tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reversal_zones', '0004_reversalzone_stop_loss_reversalzone_target'),
    ]

    operations = [
        migrations.AddField(
            model_name='reversalzone',
            name='status',
            field=models.CharField(
                max_length=20,
                default='OPEN',
                choices=[
                    ('OPEN', 'Open'),
                    ('TARGET_HIT', 'Target Hit'),
                    ('SL_HIT', 'Stop Loss Hit'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='reversalzone',
            name='status_updated_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
