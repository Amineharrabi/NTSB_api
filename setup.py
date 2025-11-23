from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def read_requirements(filename):
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ntsb",
    version="1.1.0",
    author="Amine harrabi",
    author_email="amineiiiiharrabi@gmail.com",
    description="A Python wrapper for the NTSB aviation accident database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Amineharrabi/ntsb-api",
    project_urls={
        "Bug Tracker": "https://github.com/Amineharrabi/ntsb-api/issues",
        "Documentation": "https://github.com/Amineharrabi/ntsb-api/blob/main/docs/API.md",
        "Source Code": "https://github.com/Amineharrabi/ntsb-api",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements-client.txt"),
    extras_require={
        "server": read_requirements("requirements-server.txt"),
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ntsb-api=ntsb_api.cli:main",
            "ntsb-server=ntsb_api.server.main:run_server",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)