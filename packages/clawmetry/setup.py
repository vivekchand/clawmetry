from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="clawmetry",
    version="0.1.0",
    description="Clawmetry alias package for OpenClaw Dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vivek Chand",
    author_email="vivek@openclaw.dev",
    url="https://github.com/vivekchand/openclaw-dashboard",
    python_requires=">=3.8",
    install_requires=[
        "openclaw-dashboard>=0.2.8",
    ],
    entry_points={
        "console_scripts": [
            "clawmetry=dashboard:main",
            "openclaw-dashboard=dashboard:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
    ],
    keywords="clawmetry openclaw dashboard observability ai agent monitoring",
    license="MIT",
    project_urls={
        "Bug Reports": "https://github.com/vivekchand/openclaw-dashboard/issues",
        "Source": "https://github.com/vivekchand/openclaw-dashboard",
    },
)
