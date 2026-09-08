#!/usr/bin/env python3
"""Atheris harness for `clawmetry.otlp_json.decode`.

The OTLP receiver accepts POST bodies from anything that can reach the
dashboard port, and decodes them with an in-house stdlib parser (the protobuf
extra is optional, so this path is the default one). Contract asserted:
decode either returns a request object or raises ValueError. See
`tests/fuzz/README.md`.

    pip install atheris
    python3 tests/fuzz/fuzz_otlp_json.py -atheris_runs=200000
"""

import sys

import atheris
from _contracts import OTLP_KINDS, check_otlp_json


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    # Consume the routing choices first so a mutation to the body bytes does
    # not also reshuffle which decoder path is under test.
    kind = OTLP_KINDS[fdp.ConsumeIntInRange(0, len(OTLP_KINDS) - 1)]
    content_encoding = "gzip" if fdp.ConsumeBool() else None
    check_otlp_json(fdp.ConsumeBytes(fdp.remaining_bytes()), kind, content_encoding)


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    # `_contracts` resolves because Python puts this script's directory on
    # sys.path[0] when the file is run directly, which is the only way a
    # libFuzzer harness is ever launched.
    main()
