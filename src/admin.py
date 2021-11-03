# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Product, Variant, InventoryLevel, ShopifyWebhook


class InventoryLevelAdmin(ImportExportModelAdmin):

    list_display = ('location_id', 'variant', 'available',)
    list_filter = ('location_id', )


admin.site.register(Product, ImportExportModelAdmin)
admin.site.register(Variant, ImportExportModelAdmin)
admin.site.register(InventoryLevel, InventoryLevelAdmin)
admin.site.register(ShopifyWebhook, ImportExportModelAdmin)
