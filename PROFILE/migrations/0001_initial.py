# Generated by Django 5.1.4 on 2025-01-20 09:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('CORE', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.CharField(editable=False, help_text='The unique identifier for the user. Typically provided from the client side while creating the user.', max_length=32, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, help_text='The title of the user. This can be Mr., Mrs., Dr., etc. (optional)', max_length=10, null=True)),
                ('first_name', models.CharField(help_text='The first name of the user.', max_length=50)),
                ('last_name', models.CharField(blank=True, help_text='The last name of the user. (optional)', max_length=50, null=True)),
                ('email', models.EmailField(help_text='The email of the user. Needs to be unique and a valid email.', max_length=254, unique=True)),
                ('phone', models.CharField(blank=True, help_text='The phone number of the user. (optional)', max_length=25, null=True)),
                ('dob', models.DateField(blank=True, help_text='The date of birth of the user. (optional)', null=True)),
                ('nationality', models.CharField(blank=True, help_text='The nationality of the user. (optional)', max_length=50, null=True)),
                ('address', models.TextField(blank=True, help_text='The address line of the user. Typically includes the apartment or plot number and the locality. (optional)', max_length=500, null=True)),
                ('city', models.CharField(blank=True, help_text='The city the user lives in. (optional)', max_length=50, null=True)),
                ('postal', models.CharField(blank=True, help_text='The postal code of the user. (optional)', max_length=50, null=True)),
                ('website', models.CharField(blank=True, help_text="The user's personal portfolio or blog website. (optional)", max_length=50, null=True)),
                ('profile_text', models.TextField(blank=True, help_text="The profile text of the user. This can be a short bio or a summary This would be shows on top of the user's resume. (optional)", max_length=1000, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The timestamp at which the user was created.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The timestamp at which the user was last updated.')),
                ('country', models.ForeignKey(blank=True, help_text='The country the user lives in. (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, to='CORE.country')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
