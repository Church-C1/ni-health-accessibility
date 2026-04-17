"""
Euclidean accessibility analysis functions for the Northern Ireland Healthcare Accessibility Project.

This module contains functions used specifically for the Euclidean accessibility
analysis. These functions calculate straight-line distance to the nearest hospital
and estimate the number of residents living beyond a specified Euclidean distance threshold.
"""

import geopandas as gpd


def calculate_nearest_hospital_distance(dz: gpd.GeoDataFrame, hospitals: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate the Euclidean distance from each Data Zone to its nearest hospital.

    This function creates a representative point for each Data Zone polygon and
    identifies the nearest hospital using a spatial nearest-neighbour join.
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
        Updated GeoDataFrame with:
        - 'nearest_hospital_m': Euclidean distance to nearest hospital in metres
        - 'nearest_hospital_km': Euclidean distance to nearest hospital in kilometres
    """
    dz = dz.copy()

    if dz.crs is None:
        raise ValueError("Data Zones CRS is undefined.")

    if dz.crs.is_geographic:
        raise ValueError(
            "Data Zones are in a geographic CRS (degrees). "
            "Reproject to a projected CRS before calculating Euclidean distances."
        )

    if hospitals.crs != dz.crs:
        hospitals = hospitals.to_crs(dz.crs)

    dz["zone_point"] = dz.geometry.representative_point()
    dz_points = dz.set_geometry("zone_point")

    nearest = gpd.sjoin_nearest(
        dz_points,
        hospitals[["geometry"]],
        how="left",
        distance_col="nearest_hospital_m"
    )

    dz["nearest_hospital_m"] = nearest["nearest_hospital_m"].values
    dz["nearest_hospital_km"] = (dz["nearest_hospital_m"] / 1000).round(2)

    # Remove temporary centroid column used for distance calculation
    dz = dz.drop(columns=["zone_point"], errors="ignore")

    return dz


def calculate_population_far(dz: gpd.GeoDataFrame, threshold_km: float = 20) -> gpd.GeoDataFrame:
    """
    Estimate the population living beyond a specified Euclidean distance threshold.

    This function identifies Data Zones where the Euclidean distance to the nearest
    hospital exceeds a given threshold and calculates the affected population.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries and Euclidean accessibility results.
    threshold_km : float, optional
        Euclidean distance threshold in kilometres used to define poor access.

    Returns
    -------
    gpd.GeoDataFrame
        Updated GeoDataFrame with:
        - 'affected': boolean indicating if the Data Zone exceeds the threshold
        - 'population_far': number of residents living beyond the threshold
    """
    dz = dz.copy()

    dz["affected"] = dz["nearest_hospital_km"] > threshold_km
    dz["population_far"] = dz["All usual residents"].where(dz["affected"], 0)

    return dz