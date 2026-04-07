import geopandas as gpd
import pandas as pd

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