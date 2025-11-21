"""Setup script for Focus Assistant."""

from setuptools import setup, find_packages

setup(
    name="focus-assistant",
    version="0.1.0",
    description="Your personal productivity coach powered by Claude AI",
    author="Your Name",
    py_modules=[
        'main',
        'assistant',
        'chat',
        'config',
        'routines',
        'storage',
        'tasks'
    ],
    install_requires=[
        "anthropic>=0.18.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "python-dateutil>=2.8.0",
        "pydantic>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "focus=main:cli",
        ],
    },
    python_requires=">=3.8",
)

