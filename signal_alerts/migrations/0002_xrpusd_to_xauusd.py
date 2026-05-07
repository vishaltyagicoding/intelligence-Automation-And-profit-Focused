from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('signal_alerts', '0001_initial'),
    ]

    operations = [
        # Update existing XRPUSD records to XAUUSD
        migrations.RunSQL(
            sql="UPDATE signal_alerts SET crypto = 'XAUUSD' WHERE crypto = 'XRPUSD';",
            reverse_sql="UPDATE signal_alerts SET crypto = 'XRPUSD' WHERE crypto = 'XAUUSD';",
        ),
    ]