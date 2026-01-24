"""Scripts for interacting with the flight log."""

import os
import geopandas as gpd

flight_log = os.getenv("FLIGHT_LOG_GEOPACKAGE_PATH")
if flight_log is None:
    raise KeyError(
        "Environment variable FLIGHT_LOG_GEOPACKAGE_PATH is missing."
    )

def append_flights(record_gdf):
    """Appends a GeoDataFrame of records to flights."""
    layer = "flights"

    # Ensure columns match existing structure.
    existing = gpd.read_file(
        flight_log,
        layer=layer,
        rows=0,
    )
    existing_cols = list(existing.columns)
    incoming_cols = list(record_gdf.columns)

    # Check that geometry column name matches.
    geom_col = record_gdf.geometry.name
    if geom_col not in existing_cols:
        raise ValueError(
            f"Geometry column '{geom_col}' not found in existing "
            "layer schema"
        )

    # Check for columns in new data not in current schema.
    extra_cols = set(incoming_cols) - set(existing_cols)
    if extra_cols:
        raise ValueError(
            "Incoming data has columns not present in layer "
            f"schema: {extra_cols}"
        )

    # Add missing columns from existing schema as null values.
    for col in existing_cols:
        if col not in record_gdf.columns:
            record_gdf[col] = None
            print(
                f"No value was provided for column '{col}'; setting "
                "its value to null."
            )

    # Reorder columns to match existing schema.
    gdf = record_gdf[existing_cols]

    # Append data to geopackage layer.
    gdf.to_file(
        flight_log,
        driver="GPKG",
        engine="pyogrio",
        layer=layer,
        mode="a",
    )
    print(
        f"Appended {len(record_gdf)} flights(s) to '{layer}' in {flight_log}."
    )
