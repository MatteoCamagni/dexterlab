"""
Dexterlab main module
"""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from .types.default import Dlab


def main() -> None:
    argp: ArgumentParser = ArgumentParser(
        prog="dexterlab",
        description=__doc__,
    )
    argp.add_argument(
        "-l",
        "--labdefinition",
        type=lambda x: x if Path(x).exists() else None,
        required=True,
        help="Path to dexterlab definition file. Extension required yaml or yml.",
    )

    argp.add_argument(
        "-m",
        "--mapper",
        type=str,
        required=True,
        help="Select a mapper to be used as export mapper",
    )

    argp.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Define the name of the output file",
    )

    argp.add_argument(
        "-x",
        "--export-arg",
        nargs="+",
        default=[],
        required=False,
        help="Define one or more argument to be passed to the export function of the selected mapper. Use the format 'param_name=param_value'",
    )

    # Parse command line arguments
    ns: Namespace = argp.parse_args()

    # Replace eport argument list with dictionary
    ns.export_arg = {e.split("=")[0]: e.split("=")[1] for e in ns.export_arg}

    # Create a DLab object
    tmp_dlab: Dlab = Dlab(labdef=ns.labdefinition)

    # Export the requested output
    tmp_dlab.export(mapper=ns.mapper, filename=ns.output, **ns.export_arg)


if __name__ == "__main__":
    sys.exit(main())
