"""
Road Network Preparation Functions for the Northern Ireland Healthcare Accessibility Project.

This module contains functions used to load, clean and prepare the road network
dataset for use in the network-based accessibility analysis.

The functions focus on filtering transport data, preparing geometries and
calculating segment lengths required for cost-distance modelling.
"""

import geopandas as gpd


def load_road_network(roads_path: str) -> gpd.GeoDataFrame:
    """
    Load the OSNI transport dataset.

    This function reads the OSNI transport shapefile and returns it as a
    GeoDataFrame for subsequent road network preparation and analysis.

    Parameters
    ----------
    roads_path : str
        File path to the OSNI transport shapefile.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame containing the raw OSNI transport features.
    """
    roads = gpd.read_file(roads_path)

    if roads.empty:
        raise ValueError("The road network dataset is empty.")

    return roads


def filter_road_network(roads: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Filter the OSNI transport dataset to retain road features only.

    This function removes non-road transport features, such as railways,
    based on the 'TEMA' classification field and returns a cleaned
    GeoDataFrame containing only road segments.

    Parameters
    ----------
    roads : gpd.GeoDataFrame
        Raw OSNI transport dataset.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame containing only road network features.
    """
    road_types = [
        "MOTORWAY",
        "A_CLASS",
        "DUAL_CARR",
        "B_CLASS",
        "<4M_TARRED",
        "<4M_T_OVER",
        "CL_MINOR",
        "CL_M_OVER"
    ]

    roads_clean = roads[roads["TEMA"].isin(road_types)].copy()

    if roads_clean.empty:
        raise ValueError("No road features remain after filtering.")

    return roads_clean


def prepare_road_geometries(roads: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Prepare road geometries for network analysis.

    This function explodes multipart geometries into individual features,
    removes null geometries and retains only LineString features suitable
    for network building.

    Parameters
    ----------
    roads : gpd.GeoDataFrame
        GeoDataFrame containing filtered road network features.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame containing cleaned LineString road segments.
    """
    roads = roads.copy()

    roads = roads.explode(index_parts=False).reset_index(drop=True)

    roads = roads[roads.geometry.notnull()]

    roads = roads[roads.geom_type == "LineString"].copy()

    if roads.empty:
        raise ValueError("No LineString road geometries remain after preparation.")

    return roads


def calculate_road_segment_length(roads: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate the length of each road segment in metres and kilometres.

    This function adds segment length fields to a prepared road network
    GeoDataFrame. The input data must use a projected coordinate reference
    system with units in metres.

    Parameters
    ----------
    roads : gpd.GeoDataFrame
        GeoDataFrame containing prepared LineString road segments.

    Returns
    -------
    gpd.GeoDataFrame
        Updated GeoDataFrame with:
        - 'segment_length_m': road segment length in metres
        - 'segment_length_km': road segment length in kilometres
    """
    roads = roads.copy()

    if roads.crs is None:
        raise ValueError("Road network CRS is undefined.")

    if roads.crs.is_geographic:
        raise ValueError(
            "Road network is in a geographic CRS (degrees). "
            "Reproject to a projected CRS before calculating segment lengths."
        )

    roads["segment_length_m"] = roads.geometry.length
    roads["segment_length_km"] = (roads["segment_length_m"] / 1000).round(3)

    if roads["segment_length_m"].isna().all():
        raise ValueError("Segment length calculation failed for all road geometries.")

    return roads


def remove_short_segments(
    roads: gpd.GeoDataFrame,
    min_length_m: float = 1.0
) -> gpd.GeoDataFrame:
    """
    Remove very short road segments from the network.

    This function filters out segments below a minimum length threshold,
    which are typically artefacts of data processing and can negatively
    affect network analysis.

    Parameters
    ----------
    roads : gpd.GeoDataFrame
        GeoDataFrame containing road segments with length attributes.
    min_length_m : float, optional
        Minimum segment length in metres (default = 1.0).

    Returns
    -------
    gpd.GeoDataFrame
        Cleaned GeoDataFrame with short segments removed.
    """
    roads_clean = roads[roads["segment_length_m"] >= min_length_m].copy()

    if roads_clean.empty:
        raise ValueError("All road segments were removed during short-segment filtering.")

    return roads_clean