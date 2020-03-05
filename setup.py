#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io

from setuptools import setup, find_packages

import certbot_dns_sweb


install_requires = [
    "acme>=0.31.0",  # implies requests>=2.6.0
    "certbot>=0.31.0",
    "setuptools",
    "zope.interface",
]

with io.open("README.md", "r", encoding="utf-8-sig") as rfp:
    desc = rfp.read()


setup(
    name="certbot-dns-sweb",
    version=certbot_dns_sweb.__version__,
    description="SpaceWeb DNS Authenticator plugin for Certbot",
    long_description=desc,
    long_description_content_type="text/markdown",
    url="https://github.com/andreymal/certbot-dns-sweb",
    author="andreymal",
    author_email="andriyano-31@mail.ru",
    license="MIT",
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "dns-sweb = certbot_dns_sweb.dns_sweb:Authenticator",
        ],
    },
)
