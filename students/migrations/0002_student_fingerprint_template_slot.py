# Generated manually for fingerprint_template_slot

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="student",
            name="fingerprint_hash",
        ),
        migrations.AddField(
            model_name="student",
            name="fingerprint_template_slot",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="On-sensor template slot (1–127). Device returns this slot on scan for lookup.",
                null=True,
                unique=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(127),
                ],
            ),
        ),
    ]
