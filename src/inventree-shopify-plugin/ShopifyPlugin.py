"""Plugin to integrate InvenTree with Shopify."""

from django.http.response import Http404
import requests
import json
import datetime

from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.shortcuts import redirect, render
from django import forms

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, APICallMixin


class ShopifyPlugin(APICallMixin, AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, InvenTreePlugin):
    """Main plugin class for Shopify integration."""

    NAME = 'ShopifyPlugin'
    SLUG = 'shopify'
    TITLE = "Shopify Integration App"

    NAVIGATION_TAB_NAME = "Shopify"
    NAVIGATION_TAB_ICON = 'fab fa-shopify'

    API_TOKEN = 'X-Shopify-Access-Token'
    API_TOKEN_SETTING = 'API_PASSWORD'

    SHOPIFY_API_VERSION = '2021-07'

    @property
    def api_url(self):
        return f'https://{self.get_setting("SHOP_URL")}/admin/api/{self.SHOPIFY_API_VERSION}'

    def _fetch_levels(self):
        from .models import Variant, InventoryLevel

        levels = self.api_call('inventory_levels', arguments={'inventory_item_ids': [a.inventory_item_id for a in Variant.objects.all()]})
        if 'errors' in levels:
            raise ValueError('Errors where found', levels['errors'])
        # create levels in db
        for level in levels:
            lvl, _ = InventoryLevel.objects.get_or_create(
                variant=Variant.objects.get(inventory_item_id=level.get('inventory_item_id')),
                location_id=level.get('location_id'),
                defaults={
                    'available': level.get('available'),
                }
            )
            lvl.updated_at = datetime.datetime.fromisoformat(level.get('updated_at'))
            lvl.available = level.get('available')
            lvl.save()

    def _fetch_products(self):
        from .models import Product, Variant

        products = self.api_call('products')
        if 'errors' in products:
            raise ValueError('Errors where found', products['errors'])
        # create products in db
        for product in products:
            Product.objects.update_or_create(
                id=product.get('id'),
                defaults={
                    'title': product.get('title'),
                    'body_html': product.get('body_html'),
                    'vendor': product.get('vendor'),
                    'product_type': product.get('product_type'),
                    'handle': product.get('handle'),
                    'created_at': datetime.datetime.fromisoformat(product.get('created_at')),
                    'updated_at': datetime.datetime.fromisoformat(product.get('updated_at')),
                    'published_at': datetime.datetime.fromisoformat(product.get('published_at')),
                }
            )

        # create variants in db
        for p in products:
            for var in p['variants']:
                if not Variant.objects.filter(inventory_item_id=var.get('inventory_item_id')).exists():
                    Variant.objects.create(
                        inventory_item_id=var.get('inventory_item_id'),
                        title=var.get('title'),
                        sku=var.get('sku'),
                        barcode=var.get('barcode'),
                        price=var.get('price'),
                        created_at=datetime.datetime.fromisoformat(var.get('created_at')),
                        updated_at=datetime.datetime.fromisoformat(var.get('updated_at')),
                        product_id=p.get('id'),
                    )

    # region views
    def view_index(self, request):
        """a basic overview"""
        from .models import Product, InventoryLevel

        try:
            self._fetch_products()
            self._fetch_levels()
        except ValueError:
            if request.user.is_superuser:
                # TODO @matmair send a notification to superusers to fix setup
                return redirect(self.settings_url)
            raise Http404(_('Plugin is not configured correctly'))

        context = {
            'products': Product.objects.all(),
            'levels': InventoryLevel.objects.all(),
        }
        return render(request, 'shopify/index.html', context)

    def view_increase(self, request, pk, location):
        """a basic overview"""
        class IncreaseForm(forms.Form):
            amount = forms.IntegerField(required=True, help_text=_('New level for this level'))

        context = {'pk': pk, }

        if request.method == 'GET':
            form = IncreaseForm()
        else:
            form = IncreaseForm(request.POST)

            if form.is_valid():
                # increase stock
                response = self.api_call(
                    endpoint='inventory_levels/set.json',
                    data={
                        "location_id": location,
                        "inventory_item_id": pk,
                        "available": form.cleaned_data['amount']
                    },
                    get=False
                )
                if 'inventory_level' in response:
                    return redirect(f'{self.internal_name}index')
                context['error'] = _('API call was not sucessfull')

        context['form'] = form
        return render(request, 'shopify/increase.html', context)

    def view_webhooks(self, request):
        context = {
            'webhooks': self._webhook_check(request.get_host())
        }
        return render(request, 'shopify/webhooks.html', context)

    def _webhook_check(self, host):
        # collect current hooks
        target_topics = [
            'inventory_levels/update',
            'orders/updated',
            'orders/edited',
        ]
        webhooks = self.api_call('webhooks')

        # process current hooks
        webhooks_topics = []
        webhooks_wrong_hooks = []
        for item in webhooks:
            if host in item.get('address', ''):
                webhooks_topics.append(item.get('topic', ''))
            else:
                id = item.get('id', None)
                if id:
                    webhooks_wrong_hooks.append(id)
        changed = False

        # delete hooks
        for item in webhooks_wrong_hooks:
            self._webhook_delete(item)

        # add hooks
        for topic in target_topics:
            if topic not in webhooks_topics:
                self._webhook_create(host, topic)
                changed = True

        # return all hooks
        if changed:
            return self.api_call('webhooks')
        return webhooks

    def _webhook_create(self, hostname, topic):
        from .models import ShopifyWebhook

        webhook = ShopifyWebhook.objects.create(name=f'{self.slug}_{topic}')
        response = self.api_call(
            endpoint='webhooks.json',
            data={"webhook": {
                "topic": topic,
                "address": f'https://{hostname}/api/webhook/{webhook.endpoint_id}/',
                "format": "json",
            }},
            get=False
        )
        if not response.get('webhook', False):
            raise KeyError(response)
        webhook.shopify_webhook_id = response['webhook'].get('id', None)
        webhook.save()
        return True

    def _webhook_delete(self, id):
        self.api_call(
            endpoint=f'webhooks/{id}.json',
            delete=True
        )
        return True
    # endregion

    def setup_urls(self):
        return [
            url(r'increase/(?P<location>\d+)/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
            url(r'webhook/', self.view_webhooks, name='webhooks'),
            url(r'^', self.view_index, name='index'),
        ]

    SETTINGS = {
        'API_KEY': {
            'name': _('API Key'),
            'description': _('API key for your private app'),
            'default': 'a key',
            'protected': True,
        },
        'API_PASSWORD': {
            'name': _('API Passwort'),
            'description': _('API password for your private app'),
            'default': 'a password',
            'protected': True,
        },
        'SHOP_URL': {
            'name': _('Shop url'),
            'description': _('URL for your shop instance'),
            'default': 'test.myshopify.com',
        },
        'API_SHARED_SECRET': {
            'name': _('API Shared Secret'),
            'description': _('API shared secret for your private apps webhooks'),
            'default': 'a shared key',
            'protected': True,
        },
    }

    NAVIGATION = [
        {'name': 'Product overview', 'link': 'plugin:shopify:index'},
    ]
