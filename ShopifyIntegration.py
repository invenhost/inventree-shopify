"""sample implementations for IntegrationPlugin"""
from django.http.response import JsonResponse
import requests
import json

from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.shortcuts import redirect, render
from django import forms

from plugins.integration import AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, IntegrationPluginBase


class ShopifyIntegrationPlugin(AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, IntegrationPluginBase):
    """
    Sample integration plugin for shopify
    """
    AUTHOR = "Matthias J Mair"
    PUBLISH_DATE = "1212-12-12"
    VERSION = "0.0.1"
    WEBSITE = "https://github.com/matmair/ShopifyIntegrationPlugin"

    PLUGIN_NAME = "ShopifyIntegrationPlugin"
    PLUGIN_SLUG = "shopify"
    PLUGIN_TITLE = "Shopify App"

    NAVIGATION_TAB_NAME = "Shopify"
    NAVIGATION_TAB_ICON = 'fab fa-shopify'

    SHOPIFY_API_VERSION = '2021-07'

    @property
    def endpoint_url(self):
        return f'https://{self.get_setting("SHOP_URL")}/admin/api/{self.SHOPIFY_API_VERSION}'

    @property
    def api_headers(self):
        return {'X-Shopify-Access-Token': self.get_setting("API_PASSWORD"), 'Content-Type': 'application/json'}

    def build_url_args(self, arguments):
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(self, name=None, endpoint=None, arguments=None, data=None, get:bool = True):
        if endpoint is None:
            endpoint = f'{name}.json'
        if arguments:
            endpoint += self.build_url_args(arguments)

        kwargs = {
            'url': f'{self.endpoint_url}/{endpoint}',
            'headers': self.api_headers,
        }
        if data:
            kwargs['data'] = json.dumps(data)

        response = requests.get(**kwargs) if get else requests.post(**kwargs)
        if name:
            return response.json()[name]
        return response.json()

    # region views
    def view_index(self, request):
        """a basic overview"""
        products = self.api_call('products')
        variant_ids = []
        [[variant_ids.append(v['inventory_item_id']) for v in p['variants']] for p in products]
        levels = self.api_call('inventory_levels', arguments={'inventory_item_ids': variant_ids})
        context = {
            'products': products,
            'levels': levels,
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
    # endregion

    def setup_urls(self):
        return [
            url(r'increase/(?P<location>\d+)/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
            url(r'^', self.view_index, name='index'),
        ]

    SETTINGS = {
        'API_KEY': {
            'name': _('API Key'),
            'description': _('API-key for your private app'),
            'default': 'a key',
        },
        'API_PASSWORD': {
            'name': _('API Passwort'),
            'description': _('API-password for your private app'),
            'default': 'shared path',
        },
        'SHOP_URL': {
            'name': _('Shop url'),
            'description': _('URL for your shop instance'),
            'default': 'test.myshopify.com',
        },
    }

    NAVIGATION = [
        {'name': 'Product overview', 'link': 'plugin:shopify:index'},
    ]
