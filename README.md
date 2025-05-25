# Meteo.lt API Client

This repository contains a client for the Meteo.lt API in [meteo_client.py](meteo_api/meteo_client.py) and a notebook for exploring and doing basic data analysis on fetched datain [data_analysis.ipynb](meteo_api/data_analysis.ipynb).

# Main results:

- Built a client to interact with the meteo.lt api.
- Explored what data is available in the api.
- Added metadata when fetching data observations or predictions.
- Clipped together historical data and forecast data.
- Interpolated data to 5 minute intervals.

Insights:
- Average Annual Temperature: 9.27 °C
- Average Annual Air Humidity: 77.43 %
- Average Annual Day Temperature (08:00-20:00): 10.81 °C
- Average Annual Night Temperature (20:00-08:00): 7.72 °C
- Number of rainy weekends: 34

# Installation

This project can be viewed without installation by downloading and viewing [data_analysis.html](data_analysis.html) in your browser.

To install this project the following are required:
- python ~3.12
- uv

To install the project dependencies and create a virtual environment:

```bash
uv sync
```

Then connect to the virtual environment to notebook kernel and run [data_analysis.ipynb](meteo_api/data_analysis.ipynb) sequentially.

# Project structure

├── README.md                          # Project documentation
├── pyproject.toml                     # Python project configuration and dependencies
├── .gitignore                         # Git ignore rules
├── data_analysis.html                 # Exported HTML analysis report
└── meteo_api/                         # Main package directory
    ├── __init__.py                    # Package initialization
    ├── meteo_client.py                # Meteorological API client
    └── data_analysis.ipynb            # Jupyter notebook for data analysis
