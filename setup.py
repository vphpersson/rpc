from setuptools import setup, find_packages
setup(
    name='rpc',
    version='0.11',
    packages=find_packages(),
    install_requires=[
        'msdsalgs @ git+https://github.com/vphpersson/msdsalgs.git#egg=msdsalgs',
        'ndr @ git+https://github.com/vphpersson/ndr.git#egg=ndr'
    ]
)
