from setuptools import find_packages, setup

setup(
    name="pg2ch",
    version="0.1.0",
    description="Convert PostgreSQL DDL to ClickHouse DDL",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "sqlparse>=0.4.4",
        "click>=8.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pg2ch=pg2ch.main:cli",
        ],
    },
    python_requires=">=3.8",
)
