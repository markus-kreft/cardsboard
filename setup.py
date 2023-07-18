#!/usr/bin/env python3

from setuptools import setup

setup(
    name="cardsboard",
    version="0.1",
    description="Terminal Kanban board",
    long_description=open("README.md", "rb").read().decode("utf-8"),
    long_description_content_type="text/markdown",
    author="Markus Kreft",
    author_email="mail@mkreft.de",
    url="https://github.com/markus-kreft/cardsboard",
    packages=["cardsboard"],
    entry_points={"console_scripts": ["cardsboard=cardsboard.__main__:main"]},
    data_files=[
        ("share/doc/cardsboard", ["README.md", "LICENSE"]),
    ],
    install_requires=[],
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    keywords=("kanban tui todo cards board project management"),
)
