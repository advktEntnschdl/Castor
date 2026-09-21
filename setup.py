from setuptools import find_packages, setup

setup(
    name="castor",
    version="0.1.0",
    # license="",
    description="Castor: A handy tool for performing parametric studies.",
    author="Paul Hofer",
    author_email="Paul.Hofer@uibk.ac.at",
    packages=find_packages(),
    package_data={"castor": ["share/*.pdf"]},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["dill", "numpy"],
    extras_require={"examples": ["matplotlib", "pypdf"]},
    entry_points={
        "console_scripts": [
            "castor=castor._castor:main",
        ],
    },
)
