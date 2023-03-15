from setuptools import setup

with open("README.md", "r") as f:
    readme = f.read()

setup(
    name='osmo_trade',
    version='0.1.1',
    description='SDK to trade on osmosis DEX',
    url='https://github.com/0xmercury/osmo_trade',
    long_description= readme,
    long_description_content_type="text/markdown",
    author='0xmercury',
    author_email='osmocosmo2@gmail.com',
    license='Apache License 2.0',
    packages=['osmo_trade', 'osmo_trade._pools'],
    package_data = {
        '': ['_pools/']
    },

    classifiers=[
        "Intended Audience :: Developers",
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
    ],
    project_urls={
        "Source": "https://github.com/0xmercury/osmo_trade",
    }
)
