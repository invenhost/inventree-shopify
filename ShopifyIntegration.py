"""sample implementations for IntegrationPlugin"""
import requests

from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.shortcuts import render
from django import forms

from plugins.integration import AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, IntegrationPluginBase


class ShopifyIntegrationPlugin(AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, IntegrationPluginBase):
    """
    Sample integration plugin for shopify
    """
    PLUGIN_NAME = "ShopifyIntegrationPlugin"

    SHOPIFY_API_VERSION = '2021-07'

    @property
    def endpoint_url(self):
        return f'https://{self.get_setting("API_KEY")}:{self.get_setting("API_SHARED")}@{self.get_setting("SHOP_URL")}/admin/api/{self.SHOPIFY_API_VERSION}'

    def build_url_args(self, arguments):
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def get_api_response(self, name, endpoint=None, arguments=None):
        if endpoint is None:
            endpoint = f'{name}.json'
        if arguments:
            endpoint += self.build_url_args(arguments)
        api_url = f'{self.endpoint_url}/{endpoint}'
        response = requests.get(api_url)
        return response.json()[name]

    # region views
    def view_index(self, request):
        """a basic overview"""
        products = self.get_api_response('products')
        variant_ids = []
        [[variant_ids.append(v['inventory_item_id']) for v in p['variants']] for p in products]
        levels = self.get_api_response('inventory_levels', arguments={'inventory_item_ids': variant_ids})
        context = {
            'products': products,
            'levles': levels,
        }
        return render(request, 'shopify/index.html', context)

    def view_increase(self, request, pk):
        """a basic overview"""
        class IncreaseForm(forms.Form):
            pk_inp = forms.CharField(initial=pk, widget=forms.HiddenInput())
            amount = forms.IntegerField(required=True, help_text=_('How much should the level in- / decreased?'))

        if request.method == 'GET':
            form = IncreaseForm()
        else:
            form = IncreaseForm(request.POST)

        return render(request, 'shopify/increase.html', {'pk': pk, 'form': form})
    # endregion

    def setup_urls(self):
        return [
            url(r'increase/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
            url(r'^', self.view_index, name='index'),
        ]

    SETTINGS = {
        'API_KEY': {
            'name': _('API Key'),
            'description': _('Enable PO functionality in InvenTree interface'),
            'default': 'a key',
        },
        'API_SHARED': {
            'name': _('API Shared'),
            'description': _('Enable PO functionality in InvenTree interface'),
            'default': 'shared path',
        },
        'SHOP_URL': {
            'name': _('Shop url'),
            'description': _('Enable PO functionality in InvenTree interface'),
            'default': 'test.myshopify.com',
        },
    }

    NAVIGATION = [
        {'name': 'Product overview', 'link': 'plugin:ShopifyIntegrationPlugin:index'},
    ]
