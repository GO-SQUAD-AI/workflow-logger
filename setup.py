#!/usr/bin/env python3
"""Setup script for workflow-logger package."""

from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="workflow-logger",
    version="0.1.0",
    description="Axiom logging utility for error tracking and monitoring",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Squad",
    author_email="",
    url="https://github.com/GO-SQUAD-AI/workflow-logger",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    keywords="logging axiom monitoring error-tracking workflow",
    packages=find_packages(include=["workflow_logger", "workflow_logger.*"]),
    python_requires=">=3.8",
    install_requires=[
        "axiom-py>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/GO-SQUAD-AI/workflow-logger/issues",
        "Source": "https://github.com/GO-SQUAD-AI/workflow-logger",
    },
)