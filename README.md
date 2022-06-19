# ShopifyIntegrationPlugin

**THIS PLUGIN IS CURRENTLY BROKEN AS THE PLUGIN PR IS BEEING REFACTORED**

This is a first sample implementation for the new IntegrationPlugins for [https://github.com/inventree/InvenTree/](InvenTree).

## Installation

1. Make sure plugins are activated and install this plugin via pip into the same enviroment.
2. Add a private app to your Shopify store (please register as a dev and use a development store. This is a PoC - not for production stores)
3. Go to the InvenTree settings and fill in the settings for the ShopifyIntegrationPlugin from your new private app.
4. Check out the new navigation tab.

## Caveat

Your instance must be reachable for webhooks from Shopify so use ngrok or something like that to expose your instance with HTTPS.
Open your instance on that URL for the first setup.

## State of the code

This code is bad. It is neither optimized nor is it CI/Cd ready or covered in any way.
I use this Plugin as a PoC to show what will be possible with the new system.

## Contribute

The whole plugin system is currently not even in the dev branch.
Feel free to submit issues or just send me a mail to code AT mjmair DOT com

## Built and ship
1. Ammend version.yml
2. 'python3 -m build'
3. 'python3 -m twine upload --repository testpypi dist/*'

## License

This code is licensed under MIT.
