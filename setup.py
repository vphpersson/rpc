from setuptools import setup, find_packages
setup(
    name='rpc',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'msdsalgs @ git+ssh://git@github.com/vphpersson/msdsalgs.git#egg=msdsalgs',
        'ndr @ git+ssh://git@github.com/vphpersson/ndr.git#egg=ndr'
    ]
)
