import re
from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Single source of truth: __version__ in dashboard.py
with open("dashboard.py", "r", encoding="utf-8") as f:
    version = re.search(r'__version__\s*=\s*"(.+?)"', f.read()).group(1)

# Single source of truth: FREE_RUNTIMES | PAID_RUNTIMES in
# clawmetry/entitlements.py. Parsed rather than imported because setup.py
# runs before the package is installed. Keeping the PyPI summary derived
# means it cannot go stale when a runtime lands (it said 12 while the
# catalogue said 20 until 2026-08-15).
with open("clawmetry/entitlements.py", "r", encoding="utf-8") as f:
    _ent_src = f.read()
runtime_count = sum(
    len(re.findall(r'"[a-z0-9_]+"', re.search(block, _ent_src, re.S).group(1)))
    for block in (
        r"FREE_RUNTIMES = frozenset\(\{(.*?)\}\)",
        r"PAID_RUNTIMES = frozenset\(\s*\{(.*?)\}\s*\)",
    )
)
assert runtime_count > 1, "failed to parse runtime catalogue from entitlements.py"

setup(
    name="clawmetry",
    version=version,
    description=(
        f"ClawMetry - Real-time observability for {runtime_count} AI agent runtimes "
        "(OpenClaw, NVIDIA NemoClaw, Claude Code, Codex & more)"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vivek Chand",
    author_email="vivek@clawmetry.com",
    url="https://github.com/vivekchand/clawmetry",
    # dashboard.py stays a top-level module so `python -m dashboard` and
    # existing import-paths keep working. routes/ and helpers/ are top-level
    # packages it imports at module load; they must ship in the wheel.
    py_modules=["dashboard"],
    # The repo's own test suite is EXCLUDED from the distribution. It was 39%
    # of the wheel (11.3 MB uncompressed, 958 of 1299 entries in 0.12.756) that
    # every `pip install clawmetry` downloaded and unpacked, and nothing in the
    # shipped code imports it.
    #
    # It was also a correctness problem, which is the part that actually
    # matters. Several suites resolve repo-relative paths -- `verification/`,
    # `scripts/`, `.github/workflows/` -- that are deliberately NOT packaged.
    # Shipped inside a wheel those tests cannot pass no matter what a user
    # does, and a check with no path to green is a trap: it teaches people that
    # red is normal, or invites someone to weaken the assertion instead.
    # The compliant fix is to stop shipping them, not to loosen them.
    #
    # CI is unaffected: the eval gate installs with `pip install -e .` and
    # reads `tests/...` from the checkout, and the wheel-asset gate asserts
    # runtime assets and imports, never the test package.
    # ``benchmarks`` ships in the wheel on purpose (it is ~25KB of pure Python
    # and pulls in nothing extra). The overhead figures we publish are only
    # worth something if a reader can reproduce them, and shipping the harness
    # means `pip install clawmetry` is enough to run
    # `python -m benchmarks.overhead` on your own machine. Cloning first would
    # be one more reason not to check.
    packages=find_packages(exclude=["tests", "tests.*"]) + ["routes", "helpers"],
    # static/ and templates/ now live INSIDE the clawmetry package so they
    # ship via package_data (wheel-safe). Flask is configured in dashboard.py
    # to find them via os.path.dirname(clawmetry.__file__).
    package_data={
        "clawmetry": [
            "resources/*.sh",
            "py.typed",
            "static/**/*",
            "static/**/*.*",
            # v2 React SPA bundle (pre-built by `cd frontend && npm run build`
            # before publishing). Shipped inside the wheel so end users never
            # see a Node toolchain.
            "static/v2/dist/index.html",
            "static/v2/dist/assets/*",
            "templates/**/*",
            "templates/**/*.*",
        ],
        "routes":  ["*.py"],
        "helpers": ["*.py"],
        "clawmetry.v2": ["*.py"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0,<4",
        "waitress>=2.0",
        "cryptography>=3.0",
        # cffi 2.0.0 introduced a Python 3.9 finalizer regression that causes
        # a SIGSEGV at sys.exit() when argparse prints --help text, crashing
        # `clawmetry uninstall --help` on py3.9. Pin below 2.0 until cffi
        # ships a fix upstream. See issue #5108.
        "cffi<2",
        # Local store at ~/.clawmetry/clawmetry.duckdb. Holds events,
        # sessions, memory, heartbeats, system snapshots, traces. ~14 MB
        # wheel; columnar storage gives 10-100x speed vs SQLite for the
        # dashboard's GROUP BY/time-window workloads (epic #964).
        "duckdb>=0.10",
        # Cloud cold-data relay tunnel (epic #964 phase 3b). ~100 KB pure
        # Python. Was previously in extras_require["relay"]; the opt-in
        # made cloud users silently miss the relay. Now base install so
        # `pip install clawmetry && clawmetry connect` "just works".
        "websocket-client>=1.6",
        # OS trust store for TLS (Windows CryptoAPI / macOS Security /
        # Linux CA dir) -- makes corporate TLS-interception root CAs
        # (Zscaler/Netskope/Palo Alto) "just work" without certifi hacks.
        # Needs 3.10+; 3.8/3.9 fall through to certifi below.
        'truststore>=0.8; python_version >= "3.10"',
        # The second rung of that same ladder, and the only one available
        # on 3.8/3.9 where truststore cannot install. Without a usable
        # trust store, every outbound HTTPS call (cloud sync, licence
        # checks, the install and desktop-open pings) fails with
        # CERTIFICATE_VERIFY_FAILED on any interpreter whose OpenSSL has
        # no CA bundle -- a python.org install whose certificate step was
        # never run is the common case. The pings swallow their own
        # errors so that a network problem cannot break a launch, which
        # means that failure is SILENT: no traceback, no report, just an
        # endpoint that never hears from those machines. ~160 KB, pure
        # data, no transitive deps. See docs/TELEMETRY.md.
        "certifi>=2024.2.2",
    ],
    extras_require={
        "otel": ["opentelemetry-proto>=1.20.0", "protobuf>=4.21.0"],
        # Kept for back-compat with `pip install clawmetry[relay]` calls
        # in old install scripts. No-op in 0.12.166+.
        "relay": [],
        # Optional DeepEval metric engine (clawmetry/deepeval_bridge.py).
        # Heavy on purpose-built installs only: deepeval pulls ~70 transitive
        # packages, so it must never move into install_requires. <5 pins out
        # the fast-moving major; 3.10+ marker because deepeval needs >=3.9
        # and its posthog pin needs >=3.10.
        "deepeval": ['deepeval>=4.1,<5; python_version >= "3.10"'],
    },
    entry_points={
        "console_scripts": [
            "clawmetry=clawmetry.cli:main",
            # legacy: "clawmetry=dashboard:main",
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
    keywords=(
        "clawmetry observability monitoring dashboard "
        "ai agent llm llm-observability opentelemetry cost-tracking "
        "claude-code codex cursor github-copilot gemini-cli cline openhands openworker "
        "opencode aider goose qwen devin kimi grok n8n antigravity deepseek "
        "hermes exo openclaw nemoclaw nanoclaw picoclaw moltbot"
    ),
    license="MIT",
    project_urls={
        "Homepage": "https://clawmetry.com",
        "Bug Reports": "https://github.com/vivekchand/clawmetry/issues",
        "Source": "https://github.com/vivekchand/clawmetry",
    },
)
