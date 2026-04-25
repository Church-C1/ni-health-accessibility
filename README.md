# Healthcare Accessibility in Northern Ireland: A Comparison of Euclidean and Network-Based Accessibility Measures

![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Complete-success)

This project analyses access to hospitals across Northern Ireland using two approaches:

- Euclidean (straight-line distance)
- Network-based accessibility (cost-distance accessibility index derived from the road network)

It demonstrates how methodological choice influences the identification of areas with relatively poor access to healthcare.

---

## Project Overview

This analysis focuses on hospitals as a proxy for healthcare accessibility. Healthcare accessibility is often assessed using simple distance-based measures, which can oversimplify how accessibility is shaped by the structure of the transport network. This project contrasts a straight-line approach with a network-based accessibility model to examine how each method classifies access to hospitals.

---

## Key Findings

- Euclidean analysis identifies ~4% of the population as having poor access  
- Network-based analysis identifies ~20% of the population as having poor access  
- Euclidean distance substantially underestimates the extent of poor accessibility
- This demonstrates that incorporating network structure significantly increases the number of areas identified as having poor accessibility.

---

## Analysis Objectives

- Calculate Euclidean distance from each Data Zone to the nearest hospital
- Derive a network-based accessibility index using the road network structure
- Identify areas with relatively poor access
- Compare results between the two methods
- Produce maps, tables, and summary outputs

---

## Repository Structure

```
ni-health-accessibility/
│
├── healthcare_access_analysis.ipynb # Main analysis notebook
├── data_prep.py # Data preparation functions
├── euclidean_analysis.py # Euclidean accessibility analysis
├── network_analysis.py # Network-based accessibility analysis
├── euclidean_interactive_map.py # Euclidean interactive map generation
├── network_interactive_map.py # Network-based interactive map generation
├── reporting_utilities.py # Supporting functions for outputs and reporting
├── README.md
├── LICENSE
├── .gitignore
└── environment.yml
```

---

## Data Requirements

The following datasets are required to run the analysis:

### 1. Population Data (Census 2021)
- **Description:** Usual resident population at Data Zone level  
- **Format:** Excel spreadsheet  
- **Source:** Northern Ireland Statistics and Research Agency (NISRA)  
- **Link:** https://www.nisra.gov.uk/publications/census-2021-person-and-household-estimates-data-zones-northern-ireland  

### 2. Data Zone Boundaries
- **Description:** Digital boundaries for Northern Ireland Data Zones  
- **Format:** ESRI Shapefile  
- **Source:** NISRA  
- **Link:** https://www.nisra.gov.uk/publications/data-zone-boundaries-gis-format  

### 3. County Boundaries
- **Description:** Northern Ireland county boundary dataset used for regional summaries  
- **Format:** ESRI Shapefile  
- **Source:** OSNI Open Data  
- **Link:** https://admin.opendatani.gov.uk/dataset/osni-open-data-50k-boundaries-ni-counties  

### 4. Road Network Data
- **Description:** OSNI 1:50,000 transport dataset including road classifications  
- **Format:** ESRI Shapefile  
- **Source:** OSNI Open Data  
- **Link:** https://admin.opendatani.gov.uk/dataset/osni-open-data-50k-transport-transport-lines  

### 5. Hospital Locations
- **Description:** Hospital locations extracted from OpenStreetMap using OSMnx  
- **Format:** GeoDataFrame (generated within the workflow)  
- **Source:** OpenStreetMap (via OSMnx)  

---

### Notes
- Some datasets require manual download before running the notebook  
- File paths in the notebook must be updated to match your local system  
- Hospital data is dynamically retrieved and does not require manual download

---

## Software Requirements

This project uses Python with the following libraries:

### Core libraries
- pandas  
- geopandas  
- matplotlib  
- folium  
- numpy  
- rasterio  
- rasterstats  
- scikit-image  
- osmnx  
- openpyxl

These libraries support data processing, spatial analysis, visualisation and 
interactive execution within the Jupyter Notebook environment.

### Environment
- jupyterlab

---

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Church-C1/ni-health-accessibility.git  
cd ni-health-accessibility  
```  

### 2. Create environment

```bash
conda env create -f environment.yml  
conda activate ni-health-accessibility  
```  


### 3. Launch Jupyter

```bash
jupyter lab  
```

### 4. Open the notebook

healthcare_access_analysis.ipynb  

Run all cells sequentially.

---

## How the Code Works

### Data preparation
Data Zones and population data are merged. Hospital locations are retrieved from OpenStreetMap and cleaned.

### Euclidean analysis
Straight-line distance to the nearest hospital is calculated and a threshold is applied to identify poor access.

### Network analysis
The road network is processed to derive an accessibility index based on a cost-distance representation of movement across the network.

### Mapping and outputs
Interactive maps and summary tables are generated to support comparison between methods.

---

## Outputs

Running the notebook produces:

- Choropleth maps showing spatial patterns of accessibility  
- Interactive HTML maps for Euclidean and network-based results  
- Summary statistics comparing population and Data Zones classified as having poor access  
- Comparative outputs highlighting differences between the two methods  

---

## Key Concept

- Euclidean method measures **straight-line distance**
- Network method measures **relative accessibility (not physical distance)**

---

## Reproducibility Notes

To reproduce this analysis:

- All required datasets must be downloaded and stored locally  
- File paths in the notebook should be updated to match your system  
- The Conda environment must be created using the provided `environment.yml` file  
- Hospital data is retrieved dynamically from OpenStreetMap using OSMnx, so results may vary slightly depending on query timing and data updates

---

## License

This project is licensed under the MIT License.

---

## Author

Carrie Church