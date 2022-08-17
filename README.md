# inventree-shopify

This is a first sample implementation for the new IntegrationPlugins for [InvenTree]([InvenTree](https://github.com/inventree/InvenTree/)).

## Installation

1. Make sure plugins are activated and install this plugin via pip into the same enviroment.
2. Add a private app to your Shopify store (please register as a dev and use a development store. This is a PoC - not for production stores)
3. Go to the InvenTree settings and fill in the settings for the plugin from your new private app.
4. Check out the new navigation tab.

## Caveat

Your instance must be reachable for webhooks from Shopify so use ngrok or something like that to expose your instance with HTTPS.
Open your instance on that URL for the first setup.

## State of the code

This code is currently in the PoC phase. While it works it only provides simpel features - I am open for suggestions.

## Contribute

Feel free to submit issues or just send me a mail to code AT mjmair DOT com

## Built and ship
1. Ammend version in pyproject.toml
2. 'python3 -m build'
3. 'python3 -m twine upload --repository testpypi dist/*'

## License

This code is licensed under MIT.
