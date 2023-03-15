from setuptools import setup

setup(
    name='osmo_trade',
    version='0.1.0',    
    description='SDK to trade on osmosis DEX',
    url='https://github.com/0xmercury/osmo_trade',
    author='0xmercury',
    author_email='osmocosmo2@gmail.com',
    license='Apache License 2.0',
    packages=['osmo_trade', 'osmo_trade._pools'],
    package_data = {
        '': ['_pools/']
    },

    classifiers=[
        'Intended Audience :: Trading',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
    ],
)
