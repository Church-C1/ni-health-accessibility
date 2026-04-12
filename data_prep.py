"""
Shared data preparation functions for the Northern Ireland Healthcare Accessibility Project.

This module contains reusable functions for loading and preparing core project
datasets, including Data Zone boundaries, population data and hospital locations.
These functions are shared by both the Euclidean and network-based analyses.
"""

import geopandas as gpd
import pandas as pd
import osmnx as ox


def load_and_merge_datazones(dz_path: str, pop_path: str) -> gpd.GeoDataFrame:
    """
    Load Northern Ireland Data Zone boundaries and merge them with population data.

    This function reads a shapefile containing Data Zone polygons and an Excel file
    containing population statistics, then joins them into a single GeoDataFrame
    using a common geographic identifier (DZ2021_cd).

    Parameters
    ----------
    dz_path : str
        File path to the Data Zone shapefile.
    pop_path : str
        File path to the population Excel dataset.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries with associated population data.
    """
    dz = gpd.read_file(dz_path)

    pop = pd.read_excel(
        pop_path,
        sheet_name="DZ",
        skiprows=5
    )

    dz = dz.merge(
        pop,
        left_on="DZ2021_cd",
        right_on="Geography Code"
    )

    return dz


def get_hospitals_from_osm(dz: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retrieve hospital locations from OpenStreetMap within the extent of the study area.

    This function converts the Data Zone geometries to WGS84, extracts the study
    area bounding box and queries OpenStreetMap using OSMnx to retrieve features
    tagged as hospitals.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame of hospital locations retrieved from OpenStreetMap.
    """
    dz_wgs84 = dz.to_crs(epsg=4326)
    bbox = dz_wgs84.total_bounds

    hospitals = ox.features_from_bbox(
        bbox=bbox,
        tags={"amenity": "hospital"}
    )

    if hospitals.empty:
        raise ValueError(
            "No hospital features were returned from OpenStreetMap for the study area."
        )

    return hospitals


def clean_hospitals(hospitals: gpd.GeoDataFrame, dz: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Clean and standardise hospital geometries and align them with the study area.

    This function removes invalid geometries, retains valid hospital geometry types,
    converts them to representative points, reprojects them to match the study area
    CRS and filters the dataset to hospitals located within the study area.

    Parameters
    ----------
    hospitals : gpd.GeoDataFrame
        Raw hospital data retrieved from OpenStreetMap.
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries.

    Returns
    -------
    gpd.GeoDataFrame
        Cleaned GeoDataFrame of hospital point locations within the study area.
    """
    hospitals = hospitals[hospitals.geometry.notnull()]

    hospitals = hospitals[
        hospitals.geometry.type.isin(["Point", "Polygon", "MultiPolygon"])
    ]

    hospitals["geometry"] = hospitals.geometry.representative_point()

    hospitals = hospitals.to_crs(dz.crs)

    study_area = dz.union_all() if hasattr(dz, "union_all") else dz.unary_union

    hospitals = hospitals[hospitals.intersects(study_area)]

    if hospitals.empty:
        raise ValueError(
            "No valid hospital geometries remain after cleaning and filtering."
        )

    return hospitals