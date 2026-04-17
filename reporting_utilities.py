"""
Functions for summarising and formatting analysis outputs,
including regional summary tables used in Euclidean and
network-based accessibility analysis.
"""

import pandas as pd


def summarise_by_region(
    df: pd.DataFrame,
    group_col: str,
    population_col: str,
    affected_col: str,
    affected_flag_col: str
) -> pd.DataFrame:
    """
    Summarise accessibility results by a regional grouping.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing accessibility results.
    group_col : str
        Column used to group data (e.g. county or council).
    population_col : str
        Column representing total population.
    affected_col : str
        Column representing population in poor-access areas.
    affected_flag_col : str
        Boolean column indicating whether a Data Zone is classified as poor access.

    Returns
    -------
    pd.DataFrame
        Summary table with population and Data Zone statistics by region.
    """

    summary = (
        df.groupby(group_col)
        .agg(
            total_population=(population_col, "sum"),
            affected_population=(affected_col, "sum"),
            total_datazones=(affected_flag_col, "size"),
            affected_datazones=(affected_flag_col, "sum")
        )
        .reset_index()
    )

    # Calculate percentage of population affected
    summary["pct_population_affected"] = (
        summary["affected_population"] / summary["total_population"] * 100
    ).round(2)

    # Calculate percentage of Data Zones affected
    summary["pct_datazones_affected"] = (
        summary["affected_datazones"] / summary["total_datazones"] * 100
    ).round(2)

    # Sort by affected population (descending)
    summary = summary.sort_values(
        "affected_population", ascending=False
    ).reset_index(drop=True)

    return summary


def format_summary_table(
    summary_df: pd.DataFrame,
    region_label: str
) -> pd.DataFrame:
    """
    Format a regional summary table for presentation.

    Parameters
    ----------
    summary_df : pd.DataFrame
        Summary DataFrame returned by summarise_by_region().
    region_label : str
        Display label for the grouping column (e.g. "County" or "Council").

    Returns
    -------
    pd.DataFrame
        Formatted summary table with renamed columns and formatted percentages.
    """

    formatted = summary_df.copy()

    # Rename first column (group column) and metrics for readability
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

    # Convert index to 1-based numbering for display
    formatted.index = formatted.index + 1

    # Format percentage columns
    formatted["% Pop. Affected"] = formatted["% Pop. Affected"].map("{:.2f}".format)
    formatted["% Zones Affected"] = formatted["% Zones Affected"].map("{:.2f}".format)

    return formatted


def get_worst_datazones(
    df: pd.DataFrame,
    sort_col: str,
    columns: list[str],
    rename_map: dict[str, str],
    ascending: bool = False,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Identify and format the most extreme Data Zones based on a specified metric.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing accessibility results.
    sort_col : str
        Column used to rank Data Zones (e.g. distance or accessibility index).
    columns : list[str]
        List of columns to include in the output table.
    rename_map : dict[str, str]
        Dictionary mapping original column names to display names.
    ascending : bool, optional
        Sort order. False = worst values first (default).
    top_n : int, optional
        Number of rows to return (default is 10).

    Returns
    -------
    pd.DataFrame
        Formatted table of the most extreme Data Zones.
    """

    required_cols = [sort_col] + columns
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise KeyError(f"Missing required columns for worst Data Zone table: {missing}")

    if df.empty:
        raise ValueError("Input dataset is empty.")

    worst = (
        df.sort_values(sort_col, ascending=ascending)[columns]
        .head(top_n)
        .reset_index(drop=True)
    )

    # Rename columns for display in output table
    worst = worst.rename(columns=rename_map)

    # Convert index to 1-based numbering
    worst.index = worst.index + 1

    return worst