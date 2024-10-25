import os
from setuptools import setup, find_packages

# Read the long description from README.rst
with open("README.rst", "r", encoding="utf-8") as f:
    long_descr = f.read()

# Read the version from the VERSION file
version = None
version_file = "VERSION"
if os.path.exists(version_file):
    with open(version_file, "r", encoding="utf-8") as handle:
        version = handle.read().strip()

# Ensure that the version was found
if not version:
    raise RuntimeError("VERSION file not found or empty.")

# Define package metadata directly
setup(
    name="FantraxAPI",
    version=version,
    description="Your package description here.",
    long_description=long_descr,
    long_description_content_type="text/x-rst",  # Specify content type if using reStructuredText
    url="https://github.com/meisnate12/FantraxAPI",
    author="Your Name",
    author_email="your.email@example.com",
    license="MIT",  # Replace with your license
    packages=find_packages(),
    python_requires=">=3.8",
    keywords=["fantraxapi", "fantrax", "fantasy", "wrapper", "api"],
    install_requires=[
        "requests",
        "setuptools"
    ],
    project_urls={
        "Documentation": "https://fantraxapi.metamanager.wiki",
        "Funding": "https://github.com/sponsors/meisnate12",
        "Source": "https://github.com/meisnate12/FantraxAPI",
        "Issues": "https://github.com/meisnate12/FantraxAPI/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ]
)
