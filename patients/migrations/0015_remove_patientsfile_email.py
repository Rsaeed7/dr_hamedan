from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0014_alter_medicalrecord_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientsfile',
            name='email',
        ),
    ]
