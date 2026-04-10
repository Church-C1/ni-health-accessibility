"""
Core Analysis Functions for the Northern Ireland Healthcare Accessibility Project.
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

    This function removes invalid geometries, ensures only valid geometry types
    are retained, converts all hospital geometries to representative points,
    reprojects hospital locations to match the Data Zone CRS and filters the
    dataset to include only hospitals within the study area.

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

    study_area = dz.union_all() if hasattr(dz, "union_all") else dz.unary_union

    hospitals = hospitals[hospitals.intersects(study_area)]

    return hospitals


def calculate_nearest_hospital_distance(dz: gpd.GeoDataFrame, hospitals: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate the distance from each Data Zone to its nearest hospital.

    This function creates a representative point for each Data Zone polygon and
    identifies the nearest hospital using a spatial nearest-neighbour join.
    Distances are calculated in metres and converted to kilometres.

    IMPORTANT:
    The input GeoDataFrames must be in a projected coordinate reference system (CRS)
    with units in metres. If a geographic CRS (e.g. WGS84 / EPSG:4326) is detected,
    the function will raise an error to prevent incorrect distance calculations.

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
        - 'nearest_hospital_m': distance to nearest hospital in metres
        - 'nearest_hospital_km': distance to nearest hospital in kilometres
    """
    dz = dz.copy()

    if dz.crs is None:
        raise ValueError("Data Zones CRS is undefined.")

    if dz.crs.is_geographic:
        raise ValueError(
            "Data Zones are in a geographic CRS (degrees). "
            "Reproject to a projected CRS (e.g. EPSG:29902) before calculating distances."
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

    return dz

    
def calculate_population_far(dz: gpd.GeoDataFrame, threshold_km: float = 20) -> gpd.GeoDataFrame:
    """
    Estimate the population living beyond a specified distance from the nearest hospital.

    This function identifies Data Zones where the nearest hospital exceeds a given
    distance threshold and calculates the affected population. It also creates a
    boolean 'affected' column used for mapping and classification.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries and population data.
    threshold_km : float, optional
        Distance threshold in kilometres used to define poor access (default = 20 km).

    Returns
    -------
    gpd.GeoDataFrame
        Updated GeoDataFrame with:
        - 'affected': boolean indicating if the Data Zone is beyond the threshold
        - 'population_far': number of residents living beyond the threshold distance
    """
    dz = dz.copy()

    dz["affected"] = dz["nearest_hospital_km"] > threshold_km

    dz["population_far"] = dz["All usual residents"].where(dz["affected"], 0)

    return dz


def summarise_by_region(dz: gpd.GeoDataFrame, region_col: str) -> pd.DataFrame:
    """
    Summarise healthcare accessibility results by a regional grouping.

    This function groups Data Zones by a specified regional column, then
    calculates total population, affected population, total number of
    Data Zones, affected number of Data Zones and the percentage affected
    by both population and Data Zone count.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing Data Zone geometries and accessibility results.
    region_col : str
        Name of the column used to group the summaries
        (e.g. 'county_name' or 'LGD2014_nm').

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
    Format a regional summary table for presentation.

    Parameters
    ----------
    summary_df : pd.DataFrame
        Summary DataFrame returned by summarise_by_region().
    region_label : str
        Display label for the grouping column (e.g. 'County' or 'Council').

    Returns
    -------
    pd.DataFrame
        Formatted table with readable column names and a 1-based index.
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
    Return the most remote Data Zones by nearest hospital distance.

    Parameters
    ----------
    dz : gpd.GeoDataFrame
        GeoDataFrame containing formatted Data Zone fields.
    top_n : int, optional
        Number of rows to return (default = 10).

    Returns
    -------
    pd.DataFrame
        Table of the most remote Data Zones.
    """
    required_cols = [
        "data_zone_name",
        "county_name",
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

    worst = dz[
        required_cols
    ].sort_values(
        by="nearest_hospital_km",
        ascending=False
    ).head(top_n).reset_index(drop=True)

    worst = worst.rename(columns={
        "data_zone_name": "Data Zone",
        "county_name": "County",
        "LGD2014_nm": "Council",
        "nearest_hospital_km": "Distance to Nearest Hospital (km)",
        "All usual residents": "Population",
        "population_far": "Population Beyond 20 km"
    })

    worst.index = worst.index + 1

    worst["Distance to Nearest Hospital (km)"] = worst["Distance to Nearest Hospital (km)"].round(2)

    return worst