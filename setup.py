from setuptools import setup, find_packages

setup(
    name="instrumation",
    version="0.1.2",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pyvisa",
        "pyserial",
    ],
    description="A high-level Hardware Abstraction Layer (HAL) for RF test stations with Digital Twin support.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/abduznik/instrumation",
    author="abduznik",
    author_email="abduznik@users.noreply.github.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)