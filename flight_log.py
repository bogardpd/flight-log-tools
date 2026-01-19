"""Tools for interacting with a local GeoPackage flight log."""

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tools for interacting with a local flight log."
    )
    subparsers = parser.add_subparsers()

    # import-boarding-passes
    parser_import_boarding_passes = subparsers.add_parser(
        "import-boarding-passes",
        help="Import digital boarding passes from import folder"
    )

    # import-recent
    parser_import_recent = subparsers.add_parser(
        "import-recent",
        help="Import recent flights from Flight Historian"
    )

    # Parse arguments
    args = parser.parse_args()
    print(args)
