"""
Models for ShopifyPlugin
"""
import json

from django.db import models
from django.utils.translation import gettext_lazy as _

from .ShopifyPlugin import ShopifyPlugin
from common.models import WebhookEndpoint, VerificationMethod, WebhookMessage
from InvenTree.status_codes import StockHistoryCode


class Product(models.Model):
    """A shopify product reference"""

    id = models.IntegerField(primary_key=True, verbose_name=_('Id'))
    title = models.CharField(max_length=250, verbose_name=_('Title'))
    body_html = models.CharField(max_length=250, verbose_name=_('Body HTML'))
    vendor = models.CharField(max_length=250, verbose_name=_('Vendor'))
    product_type = models.CharField(max_length=250, verbose_name=_('Product Type'))
    handle = models.CharField(max_length=250, verbose_name=_('Handle'))
    created_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))
    updated_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))
    published_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))


class Variant(models.Model):
    """A shopify product variant reference"""

    inventory_item_id = models.IntegerField(verbose_name=_('Inventory item ID'), unique=True)
    title = models.CharField(max_length=250, verbose_name=_('Title'))
    sku = models.CharField(max_length=250, verbose_name=_('SKU'))
    barcode = models.CharField(max_length=250, verbose_name=_('Barcode'))
    price = models.CharField(max_length=250, verbose_name=_('Price'))
    created_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))
    updated_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('Product')
    )
    part = models.ForeignKey(
        'part.Part',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='ShopifyVariant',
        verbose_name=_('Part')
    )


class InventoryLevel(models.Model):
    """A shopify inventory level reference"""
    class Meta:
        unique_together = ('location_id', 'variant', )

    available = models.IntegerField(verbose_name=_('Available'))
    location_id = models.IntegerField(verbose_name=_('Location ID'))
    updated_at = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='levels',
        verbose_name=_('Variant'),
    )
    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='ShopifyInventoryLevel',
        verbose_name=_('StockItem')
    )


class ShopifyWebhook(WebhookEndpoint):
    TOKEN_NAME = "X-Shopify-Hmac-Sha256"
    VERIFICATION_METHOD = VerificationMethod.HMAC

    shopify_webhook_id = models.IntegerField(
        blank=True,
        null=True
    )

    def init(self, request, *args, **kwargs):
        super().init(request, *args, **kwargs)
        self.secret = ShopifyPlugin().get_setting('API_SHARED_SECRET')

    def process_payload(self, message, payload=None, headers=None):
        topic = headers['X-Shopify-Topic']
        if self.check_if_handled(headers):
            return False

        if topic == 'inventory_levels/update':
            # handle invetorylevel update
            update_inventory_levels(payload)
        elif topic == 'orders/edited':
            # handle order edited
            pass

        elif topic == 'orders/updated':
            # handle order update
            pass

        return True

    def check_if_handled(self, headers):
        message_id = headers['X-Shopify-Webhook-Id']
        msgs = WebhookMessage.objects.filter(endpoint=self, header__contains=message_id, worked_on=True)
        if msgs.exists():
            # this was already worked on - we think
            msg = msgs.first()
            payload = json.loads(msg.header)
            if payload.get('X-Shopify-Webhook-Id', '') == message_id:
                # now we can be sure
                return True
        return False

    def get_return(self, payload, headers=None, request=None):
        return None

def update_inventory_levels(payload:dict):
    """handle updates to inventory levles

    :param payload: pyload of webhook
    :type payload: dict
    """
    # fetch item
    item = InventoryLevel.objects.filter(variant__inventory_item_id=payload['inventory_item_id'], location_id=payload['location_id'])
    if item.exists() and item.count() == 1:
        item = item.first()
        avail = payload['available']

        # set item qty
        item.available = avail
        if item.stock_item:
            # set stock item qty
            item.stock_item.quantity = avail
            item.stock_item.save()
            # add tracking entry
            item.stock_item.add_tracking_entry(
                StockHistoryCode.STOCK_COUNT,
                None,
                notes='changed in shopify inventory',
                deltas={
                    'quantity': float(avail),
                }
            )
        item.save()
