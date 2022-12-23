from setuptools import setup


with open("README.md", "rb") as readme:
    long_description = readme.read().decode()

setup(
    name='PyBitTorrent',
    version='0.2.0',
    author='Gaffner',
    author_email='gefen102@gmail.com',
    packages=['PyBitTorrent'],
    licence='LICENSE.txt',
    description='Download torrent files according to BitTorrent specifications',
    long_description=long_description,
    install_requires=[
        'bcoding==1.5',
        'bitstring~=4.0.1',
        'rich~=12.6.0',
        'requests~=2.22.0',
        'bcoding~=1.5'
    ]

)