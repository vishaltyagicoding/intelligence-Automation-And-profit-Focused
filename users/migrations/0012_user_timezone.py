from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add timezone field to User model.
    Populated automatically from the browser (Intl.DateTimeFormat) on each login.
    Used to format timestamps in email alert notifications to the user's local time.
    """

    dependencies = [
        ('users', '0011_user_trial_status_alter_user_manual_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(
                blank=True,
                default='UTC',
                help_text='IANA timezone name (e.g. Asia/Kolkata). Set automatically from browser.',
                max_length=100,
            ),
        ),
    ]
