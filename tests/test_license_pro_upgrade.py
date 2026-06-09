"""auto_provision must UPGRADE an installed clawmetry-pro to a newer cloud wheel
(it used to return early whenever pro was importable, so nodes never upgraded —
the claude_code ai-title fix in 0.3.4 sat unused on 0.3.3), and the downloaded
wheel must keep a valid PEP-427 filename or pip rejects it."""
import io, zipfile
from clawmetry import license as L


def _wheel(version):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(f"clawmetry_pro-{version}.dist-info/METADATA",
                   f"Metadata-Version: 2.1\nName: clawmetry-pro\nVersion: {version}\n")
    import tempfile, os
    d = tempfile.mkdtemp()
    p = os.path.join(d, f"clawmetry_pro-{version}-py3-none-any.whl")
    open(p, "wb").write(buf.getvalue())
    return p


def test_ver_tuple_orders_correctly():
    assert L._ver_tuple("0.3.4") > L._ver_tuple("0.3.3")
    assert L._ver_tuple("0.3.10") > L._ver_tuple("0.3.9")
    assert L._ver_tuple("1.0.0") > L._ver_tuple("0.9.9")
    assert L._ver_tuple("bad") == (0,)


def test_wheel_file_version_reads_metadata():
    assert L._wheel_file_version(_wheel("0.3.4")) == "0.3.4"
    assert L._wheel_file_version("/nope/missing.whl") is None


def test_upgrade_decision():
    # the gate installs when the available wheel is strictly newer than installed
    installed, avail = "0.3.3", L._wheel_file_version(_wheel("0.3.4"))
    assert L._ver_tuple(avail) > L._ver_tuple(installed)   # -> upgrade
    same = L._wheel_file_version(_wheel("0.3.3"))
    assert L._ver_tuple(same) <= L._ver_tuple(installed)   # -> keep current
