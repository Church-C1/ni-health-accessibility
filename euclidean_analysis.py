"""
Euclidean accessibility analysis functions for the Northern Ireland Healthcare Accessibility Project.

This module contains functions used specifically for the Euclidean accessibility
analysis. These functions calculate straight-line distance to the nearest hospital,
identify populations living beyond a distance threshold and produce formatted
summary outputs for Euclidean accessibility results.
"""

import geopandas as gpd
import pandas as pd


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
    dz = dz.drop(columns=["zone_point"])

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


def summarise_by_region(dz: gpd.GeoDataFrame, region_col: str) -> pd.DataFrame:
    """
    Summarise Euclidean accessibility results by a regional grouping.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Euclidean accessibility results.
    region_col : str
        Name of the column used to group the summaries.

    Returns
    -------
    pd.DataFrame
        DataFrame containing summary statistics for each region.
    """
    required_cols = [region_col, "All usual residents", "population_far", "affected"]
    missing = [col for col in required_cols if col not in dz.columns]

    if missing:
        raise KeyError(f"Missing required columns for regional summary: {missing}")

    if dz.empty:
        raise ValueError("Input Data Zone dataset is empty.")

    summary = (
        dz.groupby(region_col)
        .agg(
            total_population=("All usual residents", "sum"),
            affected_population=("population_far", "sum"),
            total_datazones=("affected", "size"),
            affected_datazones=("affected", "sum")
        )
        .reset_index()
    )

    summary["pct_population_affected"] = (
        summary["affected_population"] / summary["total_population"] * 100
    ).round(2)

    summary["pct_datazones_affected"] = (
        summary["affected_datazones"] / summary["total_datazones"] * 100
    ).round(2)

    summary = summary.sort_values(
        by="affected_population",
        ascending=False
    ).reset_index(drop=True)

    return summary


def format_summary_table(summary_df: pd.DataFrame, region_label: str) -> pd.DataFrame:
    """
    Format a Euclidean regional summary table for presentation.

    Parameters
    ----------
    summary_df : pd.DataFrame
        Summary DataFrame returned by summarise_by_region().
    region_label : str
        Display label for the grouping column.

    Returns
    -------
    pd.DataFrame
        Formatted summary table.
    """
    formatted = summary_df.copy()

    first_col = formatted.columns[0]

    formatted = formatted.rename(columns={
        first_col: region_label,
        "total_population": "Total Population",
        "affected_population": "Affected Population",
        "total_datazones": "Total Zones",
        "affected_datazones": "Affected Zones",
        "pct_population_affected": "% Pop. Affected",
        "pct_datazones_affected": "% Zones Affected"
    })

    formatted.index = formatted.index + 1
    formatted["% Pop. Affected"] = formatted["% Pop. Affected"].map("{:.2f}".format)
    formatted["% Zones Affected"] = formatted["% Zones Affected"].map("{:.2f}".format)

    return formatted


def get_worst_datazones(dz: gpd.GeoDataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the most remote Data Zones by Euclidean distance to the nearest hospital.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Euclidean accessibility results.
    top_n : int, optional
        Number of rows to return.

    Returns
    -------
    pd.DataFrame
        Table of the most remote Data Zones under the Euclidean model.
    """
    required_cols = [
        "DZ2021_nm",
        "LGD2014_nm",
        "nearest_hospital_km",
        "All usual residents",
        "population_far"
    ]
    missing = [col for col in required_cols if col not in dz.columns]

    if missing:
        raise KeyError(f"Missing required columns for worst Data Zone table: {missing}")

    if dz.empty:
        raise ValueError("Input Data Zone dataset is empty.")

    worst = dz[required_cols].sort_values(
        by="nearest_hospital_km",
        ascending=False
    ).head(top_n).reset_index(drop=True)

    worst = worst.rename(columns={
        "DZ2021_nm": "Data Zone",
        "LGD2014_nm": "Council",
        "nearest_hospital_km": "Distance to Nearest Hospital (km)",
        "All usual residents": "Population",
        "population_far": "Population Beyond 20 km"
    })

    worst.index = worst.index + 1
    worst["Distance to Nearest Hospital (km)"] = worst["Distance to Nearest Hospital (km)"].round(2)

    return worst