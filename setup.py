import yaml
import setuptools
import os
import pathlib

# load info files
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("src/ShopifyIntegrationPlugin/version.yml", "r", encoding="utf-8") as fh:
    version_file = yaml.load(fh, Loader=yaml.FullLoader)


setuptools.setup(
    name=version_file['name'],
    version=version_file['version'],
    author=version_file['author'],
    author_email="info@mjmair.com",
    description="Shopify integration for InvenTree",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=version_file['website'],
    project_urls={
        "Bug Tracker": f"{version_file['website']}/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",  # Remove after final released
        "Environment :: Plugins",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering",
    ],

    install_requires=[
        'requests',
        'django',
        'pyyaml',
    ],
    extras_require={
        'dev': [
            'twine',
            'setuptools',
        ]
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    python_requires=">=3.6",
    include_package_data=True,

    entry_points={"inventree_plugins": ["ShopifyIntegrationPlugin = ShopifyIntegrationPlugin.ShopifyIntegration:ShopifyIntegrationPlugin"]},
)
