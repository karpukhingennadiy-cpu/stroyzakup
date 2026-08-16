"""Add performance indexes."""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0004_supplier_source_dadata'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='supplier',
            index=models.Index(fields=['is_active', 'supplier_type'], name='supplier_active_type_idx'),
        ),
        migrations.AddIndex(
            model_name='supplier',
            index=models.Index(fields=['source'], name='supplier_source_idx'),
        ),
        migrations.AddIndex(
            model_name='supplieraddress',
            index=models.Index(fields=['city'], name='supplier_city_idx'),
        ),
        migrations.AddIndex(
            model_name='suppliercategory',
            index=models.Index(fields=['category'], name='supplier_cat_idx'),
        ),
    ]
