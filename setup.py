from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

version = '0.1'

install_requires = [
    'bottle>=0.12',
    'gevent>=1.1',
    'prometheus_client>=0.0.18',
    # 'service-checker>=0.1.6'  # provided by deb
]

description = "A Prometheus exporter that renders metrics from requests"
"executed by service-checker."

setup(
    name='prometheus-swagger-exporter',
    version=version,
    description=description,
    long_description=README,
    author='Cole White',
    author_email='cwhite@wikimedia.org',
    #url='',
    license='GPL',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'prometheus-swagger-exporter = src.main:main'
        ]
    },
)
