"""
Core analysis functions for the Northern Ireland healthcare accessibility project.
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
        File path to the Data Zone shapefile (spatial boundaries).
    pop_path : str
        File path to the population Excel dataset (Census 2021).

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

    This function converts the Data Zone geometries to WGS84 (latitude/longitude),
    extracts the bounding box of the study area, and queries OpenStreetMap using
    OSMnx to retrieve features tagged as hospitals.

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

    return hospitals

def clean_hospitals(hospitals: gpd.GeoDataFrame, dz: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Clean and standardise hospital geometries and align them with the study area.

    This function removes invalid geometries, converts polygon geometries to
    representative points, reprojects hospital locations to match the Data Zone CRS,
    and filters the dataset to include only hospitals within the study area.

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
    hospitals = hospitals[hospitals.geometry.type.isin(["Point", "Polygon", "MultiPolygon"])]

    hospitals["geometry"] = hospitals.geometry.representative_point()

    hospitals = hospitals.to_crs(dz.crs)

    hospitals = hospitals[hospitals.intersects(dz.unary_union)]

    return hospitals

def calculate_nearest_hospital_distance(dz: gpd.GeoDataFrame, hospitals: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate the distance from each Data Zone to its nearest hospital.

    This function generates a representative point for each Data Zone polygon and
    computes the minimum straight-line (Euclidean) distance to the nearest hospital.
    Distances are calculated in metres and converted to kilometres.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries.
    hospitals : gpd.GeoDataFrame
        GeoDataFrame containing cleaned hospital point locations.

    Returns
    -------
    gpd.GeoDataFrame
        Updated GeoDataFrame with two new columns:
        - 'nearest_hospital_m': distance to nearest hospital in metres
        - 'nearest_hospital_km': distance to nearest hospital in kilometres
    """
    dz["zone_point"] = dz.geometry.representative_point()

    dz_points = dz.copy()
    dz_points = dz_points.set_geometry("zone_point")

    distances = []

    for point in dz_points.geometry:
        nearest_distance = hospitals.distance(point).min()
        distances.append(nearest_distance)

    dz["nearest_hospital_m"] = distances
    dz["nearest_hospital_km"] = dz["nearest_hospital_m"] / 1000

    return dz

def calculate_population_far(dz: gpd.GeoDataFrame, threshold_km: float = 20) -> gpd.GeoDataFrame:
    """
    Estimate the population living beyond a specified distance from the nearest hospital.

    This function identifies Data Zones where the nearest hospital exceeds a given
    distance threshold and calculates the affected population by applying a boolean mask to the population field.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries and population data.
    threshold_km : float, optional
        Distance threshold in kilometres used to define poor access (default = 20 km).

    Returns
    -------
    gpd.GeoDataFrame
        Updated GeoDataFrame with a new column:
        - 'population_far': estimated number of residents living beyond the threshold distance
    """
    dz["population_far"] = dz["All usual residents"] * (dz["nearest_hospital_km"] > threshold_km)

    return dz