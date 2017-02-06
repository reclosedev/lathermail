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
    url="https://github.com/reclosedev/lathermail/",
    version="0.4.1",
    author="Roman Haritonov",
    description="SMTP Server with API for email testing inspired by mailtrap and maildump",
    author_email="reclosedev@gmail.com",
    license="MIT",
    packages=find_packages("."),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            [
                'lathermail = lathermail.run_all:main',
            ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
        "Topic :: Communications :: Email",
    ],
    long_description=read('README.rst') + '\n\n' + read('CHANGELOG.rst'),
)
