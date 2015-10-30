import os
from setuptools import setup, find_packages

install_requires = [
    "Flask==0.10.1",
    "Flask-RESTful==0.2.12",
    "Flask-PyMongo==0.3.0",
    "pymongo==2.7.1",
    "python-dateutil==2.2",
    "SQLAlchemy==1.0.9",
    "Flask-SQLAlchemy==2.1",
]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="lathermail",
    version="0.0.1",
    author="Roman Haritonov",
    license="MIT",
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
