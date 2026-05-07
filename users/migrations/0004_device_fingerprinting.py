# Generated migration for device fingerprinting

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_emailverification_passwordreset'),
    ]

    operations = [
        # Add device fingerprinting fields to User model
        migrations.AddField(
            model_name='user',
            name='device_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='registration_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='registration_user_agent',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='trial_used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='trial_allowed',
            field=models.BooleanField(default=True),
        ),
        
        # Add device_id to EmailVerification model
        migrations.AddField(
            model_name='emailverification',
            name='device_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        
        # Create DeviceFingerprint model
        migrations.CreateModel(
            name='DeviceFingerprint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('device_id', models.CharField(db_index=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('trial_granted', models.BooleanField(default=False)),
                ('trial_count', models.IntegerField(default=0)),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('is_blocked', models.BooleanField(default=False)),
                ('block_reason', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='device_fingerprints', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'device_fingerprints',
                'ordering': ['-last_seen'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['device_id'], name='users_device_id_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['registration_ip'], name='users_registration_ip_idx'),
        ),
        migrations.AddIndex(
            model_name='devicefingerprint',
            index=models.Index(fields=['device_id'], name='device_fingerprints_device_id_idx'),
        ),
        migrations.AddIndex(
            model_name='devicefingerprint',
            index=models.Index(fields=['ip_address'], name='device_fingerprints_ip_address_idx'),
        ),
        migrations.AddIndex(
            model_name='devicefingerprint',
            index=models.Index(fields=['trial_granted'], name='device_fingerprints_trial_granted_idx'),
        ),
        migrations.AddIndex(
            model_name='devicefingerprint',
            index=models.Index(fields=['is_blocked'], name='device_fingerprints_is_blocked_idx'),
        ),
    ]
