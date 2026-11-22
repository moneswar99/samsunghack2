"""
Setup script for Samsung XR Eyes Python SDK
"""
from setuptools import setup, find_packages

setup(
    name="samsung-xr-eyes",
    version="1.0.0",
    author="DSS Srikar / Samsung XR Hackathon Track 01",
    description="Python SDK for Synthetic Eye Movement, Binocular Convergence and Virtual Camera Ground-Truth Generation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/samsung-xr-hackathon-2026/track01-gaze",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Scientific/Engineering :: Computer Vision",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
    ],
)
