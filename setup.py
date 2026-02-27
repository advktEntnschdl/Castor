from setuptools import find_packages, setup

setup(
    name="castor",
    version="0.01",
    # license="",
    description="Castor: A handy tool for performing parametric studies.",
    author="Paul Hofer",
    author_email="Paul.Hofer@uibk.ac.at",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "castor=castor._castor:main",
        ],
    },
)
