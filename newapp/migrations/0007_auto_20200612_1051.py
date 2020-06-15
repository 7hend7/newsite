# Generated by Django 3.0.6 on 2020-06-12 07:51

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('newapp', '0006_auto_20200612_1048'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='imgpage',
            name='image',
        ),
        migrations.AddField(
            model_name='imgpage',
            name='images',
            field=wagtail.core.fields.StreamField([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))], blank=True, verbose_name='Images'),
        ),
    ]