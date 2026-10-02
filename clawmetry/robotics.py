"""OSS CLI seam. Hardware implementation is distributed in ClawMetry Pro."""

def cli_main(argv=None):
    try:
        from clawmetry_pro.robotics.cli import main
    except ImportError:
        print("SO-101 tracing requires ClawMetry Pro. Activate your license and install the private package.")
        return 2
    return main(argv)
