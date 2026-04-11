"""
Road Network Analysis Functions for the Northern Ireland Healthcare Accessibility Project.
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
    for network construction.

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