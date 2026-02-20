from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Curso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, unique=True)),
                ('tipo', models.CharField(choices=[('bacharelado', 'Bacharelado'), ('licenciatura', 'Licenciatura'), ('tecnologico', 'Tecnólogo')], max_length=50)),
                ('duracao', models.CharField(max_length=50)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('link_matricula', models.URLField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['tipo', 'nome'],
            },
        ),
    ]
