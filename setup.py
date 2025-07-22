#!/usr/bin/env python3
"""
Setup script for Crypto Portfolio Dashboard
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crypto-portfolio-dashboard",
    version="1.0.0",
    author="Berry Kuipers",
    author_email="berry.kuipers@gmail.com",
    description="Advanced crypto portfolio dashboard with FIFO P&L calculations, transfer tracking, and staking rewards detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BerryKuipers/crypto-portfolio-dashboard",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-mock>=3.0",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "crypto-portfolio=portfolio.cli:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
