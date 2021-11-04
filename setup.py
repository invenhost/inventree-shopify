from setuptools import setup

setup(
    name='ShopifyIntegrationPlugin',
    version='0.0.1',
    packages=['src'],
    install_requires=[
        'requests',
        'django',
        'importlib',
    ],
    entry_points={"inventree_plugins": ["ShopifyIntegrationPlugin = src.ShopifyIntegration.ShopifyIntegrationPlugin"]},
)
