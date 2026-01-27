from setuptools import setup, find_packages

setup(
    name="instrumation",
    version="0.2.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pyvisa",
        "pyserial",
    ],
    description="A high-level hardware abstraction layer for RF test stations.",
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)