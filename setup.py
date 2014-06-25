import os
from setuptools import setup, find_packages

install_requires = [
    "Flask",
    "Flask-RESTful",
    "Flask-PyMongo",
    "python-dateutil",
]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="lathermail",
    version="0.0.1",
    author="ASD Technologies",
    license="Private",
    packages=find_packages("."),
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            [
                'lathermail = run_all:main',
            ]
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "License :: Other/Proprietary License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
    ],
)
