"""
Interactive map functions for the Northern Ireland healthcare accessibility project.

This module contains functions used to construct and style an interactive Folium map,
including Data Zone visualisation, hospital markers and map legend elements.
"""

import folium


def style_function(feature):
    """
    Define the visual style for Data Zones based on accessibility status.

    Data Zones located more than 20 km from the nearest hospital are highlighted,
    while all other zones are displayed with a neutral colour.

    Parameters
    ----------
    feature : dict
        GeoJSON feature representing a Data Zone.

    Returns
    -------
    dict
        Dictionary of style properties applied to the feature.
    """
    return {
        "fillColor": "red" if feature["properties"]["affected"] else "#cfe8f3",
        "color": "#888888",
        "weight": 0.25,
        "fillOpacity": 0.7 if feature["properties"]["affected"] else 0.45
    }


def highlight_function(feature):
    """
    Define the highlight style for Data Zones when hovered over.

    Parameters
    ----------
    feature : dict
        GeoJSON feature representing a Data Zone.

    Returns
    -------
    dict
        Dictionary of highlight style properties.
    """
    return {
        "weight": 2,
        "color": "yellow",
        "fillOpacity": 0.8
    }


def add_datazones_layer(m, dz_wgs84):
    """
    Add Data Zone polygons to the interactive map with tooltip information.

    Tooltips display key attributes including Data Zone name, Data Zone code,
    county, local council, distance to the nearest hospital (in km) and Population 
    beyond 20 km.

    Parameters
    ----------
    m : folium.Map
        Folium map object.
    dz_wgs84 : gpd.GeoDataFrame
        Data Zones converted to WGS84 coordinate reference system.

    Returns
    -------
    None
        The layer is added directly to the map.
    """
    folium.GeoJson(
        dz_wgs84,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "data_zone_name",
                "DZ2021_cd",
                "county_name",
                "LGD2014_nm",
                "nearest_hospital_km",
                "population_far"
            ],
            aliases=[
                "Data Zone Name:",
                "Data Zone Code:",
                "County:",
                "Local Council:",
                "Distance to Nearest Hospital (km):",
                "Population Beyond 20 km:"
            ],
            localize=True,
            sticky=False,
            labels=True,
        ),
        popup=None,
        name="Data Zones"
    ).add_to(m)


def add_hospital_markers(m, hospitals_wgs84):
    """
    Add hospital locations to the interactive map as styled markers.

    Hospital markers are displayed above polygon layers to ensure visibility
    and include tooltips and popups showing hospital names.

    Parameters
    ----------
    m : folium.Map
        Folium map object.
    hospitals_wgs84 : gpd.GeoDataFrame
        Hospital locations converted to WGS84 coordinate reference system.

    Returns
    -------
    None
        Markers are added directly to the map.
    """
    folium.map.CustomPane("hospital_markers").add_to(m)

    m.get_root().html.add_child(folium.Element("""
    <style>
        .leaflet-pane.hospital_markers {
            z-index: 650;
        }
    </style>
    """))

    hospital_group = folium.FeatureGroup(name="Hospitals").add_to(m)

    for _, row in hospitals_wgs84.iterrows():
        hospital_name = row.get("name", "Unnamed hospital")

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color="darkgreen",
            weight=2,
            fill=True,
            fill_color="green",
            fill_opacity=1,
            tooltip=hospital_name,
            popup=hospital_name,
            pane="hospital_markers"
        ).add_to(hospital_group)


def add_legend(m):
    """
    Add a custom legend to the interactive map.

    The legend identifies affected and non-affected Data Zones
    and shows the symbol used for hospital locations.

    Parameters
    ----------
    m : folium.Map
        Folium map object.

    Returns
    -------
    None
        The legend is added directly to the map.
    """
    legend_html = """
    <div style="
        position: fixed;
        bottom: 40px;
        left: 40px;
        z-index: 9999;
        font-size: 13px;
        background-color: white;
        border: 1px solid #888;
        border-radius: 5px;
        padding: 8px 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        white-space: nowrap;
    ">
    <b>Map key</b><br>

    <div style="margin-top:6px;">
        <span style="
            background:red;
            width:12px;
            height:12px;
            display:inline-block;
            margin-right:8px;
        "></span>
        >20 km from hospital
    </div>

    <div>
        <span style="
            background:#cfe8f3;
            width:12px;
            height:12px;
            display:inline-block;
            margin-right:8px;
        "></span>
        Within 20 km
    </div>

    <div style="margin-top:4px;">
        <span style="
            display:inline-block;
            width:12px;
            height:12px;
            margin-right:8px;
            background:green;
            border:2px solid darkgreen;
            border-radius:50%;
            vertical-align:middle;
        "></span>
        Hospital
    </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def add_tooltip_style(m):
    """
    Add custom CSS to improve tooltip formatting.

    This styling prevents line wrapping in tooltip labels and values,
    allowing the tooltip box to expand to fit longer text.
    
    Parameters
    ----------
    m : folium.Map
        Folium map object.

    Returns
    -------
    None
        The CSS is added directly to the map.
    """
    tooltip_css = """
    <style>
    .leaflet-tooltip {
        max-width: none !important;
        width: auto !important;
        white-space: nowrap !important;
    }

    .leaflet-tooltip table {
        width: auto !important;
    }

    .leaflet-tooltip th,
    .leaflet-tooltip td {
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(tooltip_css))