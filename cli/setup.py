import os
from setuptools import find_packages, setup

with open("game7dev/version.txt") as ifp:
    VERSION = ifp.read().strip()

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

# eth-brownie should be installed as a library so that it doesn't pin version numbers for all its dependencies
# and wreak havoc on the install.
os.environ["BROWNIE_LIB"] = "1"

setup(
    name="game7dev",
    version=VERSION,
    packages=find_packages(),
    install_requires=["eth-brownie", "inspector-facet", "tqdm"],
    extras_require={
        "dev": ["black", "isort", "moonworm"],
    },
    description="Development tools for Game7 smart contracts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Moonstream DAO",
    author_email="engineering@moonstream.to",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "game7dev=game7dev.cli:main",
        ]
    },
    package_data={"game7dev": ["version.txt"]},
    include_package_data=True,
)
