from setuptools import setup

setup(
    name="castor",
    version="0.01",
    # license="",
    description="Castor: A handy tool for performing parametric studies.",
    packages=["src"],
    author="Paul Hofer",
    author_email="Paul.Hofer@uibk.ac.at",
    entry_points={
        "console_scripts": [
            "castor=castor._castor:main",
        ],
    },
)
