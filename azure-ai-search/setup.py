from setuptools import find_packages, setup


def read_requirements():
    with open("requirements.txt") as req:
        return req.read().splitlines()


setup(
    name="azure-ai-search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements(),
)
