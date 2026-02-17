from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="clawmetry",
    version="0.7.0",
    description="ClawMetry - Real-time observability dashboard for OpenClaw AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vivek Chand",
    author_email="vivek@openclaw.dev",
    url="https://github.com/vivekchand/clawmetry",
    py_modules=["dashboard"],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0",
    ],
    extras_require={
        "otel": ["opentelemetry-proto>=1.20.0", "protobuf>=4.21.0"],
    },
    entry_points={
        "console_scripts": [
            "clawmetry=dashboard:main",
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
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Monitoring",
    ],
    keywords="clawmetry openclaw moltbot dashboard observability ai agent monitoring opentelemetry",
    license="MIT",
    project_urls={
        "Homepage": "https://clawmetry.com",
        "Bug Reports": "https://github.com/vivekchand/clawmetry/issues",
        "Source": "https://github.com/vivekchand/clawmetry",
    },
)
