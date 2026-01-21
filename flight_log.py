"""Tools for interacting with a local GeoPackage flight log."""

import argparse
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

def import_boarding_passes():
    """Imports digital boarding passes."""
    print("Importing digital boarding passes...")

def import_recent():
    """Finds recent flights on Flight Historian API and imports them."""
    print("Importing Flight Historian recent flights...")
    api_key_fh = os.getenv("API_KEY_FLIGHT_HISTORIAN")
    if api_key_fh is None:
        raise KeyError(
            "Environment variable API_KEY_FLIGHT_HISTORIAN is missing."
        )
    headers = {"api-key": api_key_fh}
    url = "https://www.flighthistorian.com/api/recent_flights"
    print(f"🌐 Requesting {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    json_data = response.json()
    if len(json_data) == 0:
        print("Flight Historian provided zero recent flights.")
        quit()
    for flight in json_data:
        print(flight)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tools for interacting with a local flight log."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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
    match args.command:
        case "import-boarding-passes":
            import_boarding_passes()
        case "import-recent":
            import_recent()
        case _:
            print("No command provided. See --help for commands.")
