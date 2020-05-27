from setuptools import setup

with open("README.md") as README:
    readme = str(README.read())

with open("requirements.txt") as reqs:
    install_requires = [
        line
        for line in reqs.read().split("\n")
        if line and not line.startswith(("--", "git+ssh"))
    ]
    dependency_links = [
        line
        for line in reqs.read().split("\n")
        if line and line.startswith(("--", "git+ssh"))
    ]

setup(
    name="pewtils",
    version="1.0.0",
    description="General programming utilities from Pew Research Center",
    long_description=readme,
    url="https://github.com/pewresearch/pewtils",
    author="Pew Research Center",
    author_email="info@pewresearch.org",
    install_requires=install_requires,
    dependency_links=dependency_links,
    packages=["pewtils"],
    include_package_data=True,
    keywords="utilities, link standardization, input, output, pew pew pew",
    license="GPLv2+",
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
