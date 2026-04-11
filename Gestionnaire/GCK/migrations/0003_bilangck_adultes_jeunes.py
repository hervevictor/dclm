from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GCK', '0002_alter_bilangck_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilangck',
            name='adultes_hommes',
            field=models.PositiveIntegerField(default=0, verbose_name='Adultes Hommes'),
        ),
        migrations.AddField(
            model_name='bilangck',
            name='adultes_femmes',
            field=models.PositiveIntegerField(default=0, verbose_name='Adultes Femmes'),
        ),
        migrations.AddField(
            model_name='bilangck',
            name='jeunes_hommes',
            field=models.PositiveIntegerField(default=0, verbose_name='Jeunes Hommes'),
        ),
        migrations.AddField(
            model_name='bilangck',
            name='jeunes_femmes',
            field=models.PositiveIntegerField(default=0, verbose_name='Jeunes Femmes'),
        ),
        migrations.RemoveField(
            model_name='bilangck',
            name='hommes',
        ),
        migrations.RemoveField(
            model_name='bilangck',
            name='femmes',
        ),
    ]
