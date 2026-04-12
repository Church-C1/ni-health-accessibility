"""
Euclidean Interactive Map Functions for the Northern Ireland Healthcare Accessibility Project.

This module contains functions used to construct and style an interactive Folium map
for the Euclidean accessibility analysis.

The map visualises Data Zones based on straight-line (Euclidean) distance to the
nearest hospital, highlighting areas located more than 20 km away. It also includes
hospital markers, tooltips and custom interface elements to support exploration of
Euclidean accessibility results.
"""

import folium
from folium.plugins import MarkerCluster


def style_function(feature):
    """
    Define the visual style for Data Zones based on Euclidean accessibility status.

    Data Zones located more than 20 km from the nearest hospital are highlighted
    in red, while all other zones are displayed using a neutral colour.

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
    Add Data Zone polygons to the interactive map with Euclidean accessibility attributes.

    Tooltips display key attributes including Data Zone name, Data Zone code,
    local council, Euclidean distance to the nearest hospital (in km)
    and the population living beyond 20 km.

    The function validates that all required fields are present before creating
    the map layer.

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

    required_fields = [
        "DZ2021_nm",
        "DZ2021_cd",
        "LGD2014_nm",
        "nearest_hospital_km",
        "population_far",
        "affected"
    ]

    missing = [col for col in required_fields if col not in dz_wgs84.columns]

    if missing:
        raise KeyError(f"Missing required columns for map layer: {missing}")

    folium.GeoJson(
        dz_wgs84,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "DZ2021_nm",
                "DZ2021_cd",
                "LGD2014_nm",
                "nearest_hospital_km",
                "population_far"
            ],
            aliases=[
                "Data Zone Name:",
                "Data Zone Code:",
                "Council:",
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
    Add hospital locations to the interactive map as icon-based markers.

    Hospital locations are displayed using Folium markers with a medical-style
    icon for improved visual clarity. Markers are grouped using a MarkerCluster
    to reduce visual clutter at lower zoom levels. Each marker includes a styled
    tooltip showing the hospital label and name.

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
    hospital_group = MarkerCluster(name="Hospitals").add_to(m)

    for _, row in hospitals_wgs84.iterrows():
        hospital_name = row.get("name", "Unnamed hospital")

        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=folium.Tooltip(
                f'<div style="font-size:12px;"><b>Hospital</b><br>{hospital_name}</div>',
                sticky=False
            ),
            icon=folium.Icon(
                color="green",
                icon="plus-sign",
                prefix="glyphicon"
            )
        ).add_to(hospital_group)


def add_legend(m):
    """
    Add a custom legend for Euclidean accessibility results.

    The legend identifies Data Zones located more than 20 km from the nearest
    hospital and those within 20 km, along with the symbol used for hospital
    locations.

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
        left: 10px;
        z-index: 9999;
        font-size: 13px;
        background-color: white;
        border: 1px solid #888;
        border-radius: 5px;
        padding: 8px 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        white-space: nowrap;
    ">
    <b>Map legend</b><br>

    <div style="margin-top:6px;">
        <span style="
            background:red;
            width:12px;
            height:12px;
            display:inline-block;
            margin-right:8px;
        "></span>
        More than 20 km from hospital
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
            color:green;
            font-weight:bold;
            text-align:center;
            line-height:12px;
        ">
            +
        </span>
        Hospital
    </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def add_tooltip_style(m):
    """
    Add custom CSS to improve tooltip formatting and interactive behaviour.

    This styling enhances tooltip readability, prevents text wrapping,
    removes focus outlines and defines reusable UI styling for the
    Euclidean interactive map.

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
        font-size: 12px;
        padding: 6px 8px;
    }

    .leaflet-tooltip table {
        width: auto !important;
    }

    .leaflet-tooltip th,
    .leaflet-tooltip td {
        white-space: nowrap !important;
        word-break: keep-all !important;
    }

    .leaflet-interactive:focus {
        outline: none !important;
    }

    path.leaflet-interactive:focus {
        outline: none !important;
    }

    .leaflet-marker-icon:focus {
        outline: none !important;
    }

    .leaflet-container a:focus {
        outline: none !important;
    }

    /* Reset button positioning */
    .map-btn {
        position: fixed;
        top: 95px;
        left: 10px;
        z-index: 9999;
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(tooltip_css))


def add_reset_button(m, center, zoom):
    """
    Add a reset view button to return the map to its original extent.

    The button uses a reusable CSS class for positioning, ensuring
    consistent styling and easier maintenance.

    Parameters
    ----------
    m : folium.Map
        Folium map object.
    center : list
        Initial map centre [lat, lon].
    zoom : int
        Initial zoom level.

    Returns
    -------
    None
        The button is added directly to the map.
    """
    map_name = m.get_name()

    reset_js = f"""
    <script>
    function resetMap() {{
        {map_name}.setView([{center[0]}, {center[1]}], {zoom});
    }}
    </script>
    """

    button_html = """
    <div class="map-btn">
        <button onclick="resetMap()" style="
            background-color: white;
            border: 1px solid #888;
            border-radius: 4px;
            padding: 5px 8px;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        ">
            Reset view
        </button>
    </div>
    """

    m.get_root().html.add_child(folium.Element(reset_js + button_html))


def add_metric_scale_bar(m):
    """
    Add a metric-only scale bar to the interactive map.

    This replaces the default Folium scale bar, displays distance
    in kilometres only and aligns the scale bar with other map elements.

    Parameters
    ----------
    m : folium.Map
        Folium map object.

    Returns
    -------
    None
        The scale bar is added directly to the map.
    """
    map_name = m.get_name()

    scale_js = f"""
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        function attachScaleBar() {{
            if (typeof {map_name} !== "undefined") {{
                {map_name}.whenReady(function() {{
                    L.control.scale({{
                        position: "bottomleft",
                        metric: true,
                        imperial: false
                    }}).addTo({map_name});
                }});
            }} else {{
                setTimeout(attachScaleBar, 100);
            }}
        }}
        attachScaleBar();
    }});
    </script>
    """

    scale_css = """
    <style>
    .leaflet-control-scale {
        margin-left: 10px !important;
    }
    </style>
    """

    m.get_root().html.add_child(folium.Element(scale_js + scale_css))