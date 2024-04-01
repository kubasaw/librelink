"""Constants for librelink."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "LibreLink"
DOMAIN = "librelink"
VERSION = "1.2.3"
ATTRIBUTION = "Data provided by https://libreview.com"
LOGIN_URL = "/llu/auth/login"
CONNECTION_URL = "/llu/connections"
COUNTRY = "Country"
COUNTRY_LIST = [
    "Global",
    "Arab Emirates",
    "Asia Pacific",
    "Australia",
    "Canada",
    "Germany",
    "Europe",
    "France",
    "Japan",
    "Russia",
    "United States",
]
BASE_URL_LIST = {
    "Global": "https://api.libreview.io",
    "Arab Emirates": "https://api-ae.libreview.io",
    "Asia Pacific": "https://api-ap.libreview.io",
    "Australia": "https://api-au.libreview.io",
    "Canada": "https://api-ca.libreview.io",
    "Germany": "https://api-de.libreview.io",
    "Europe": "https://api-eu.libreview.io",
    "France": "https://api-fr.libreview.io",
    "Japan": "https://api-jp.libreview.io",
    "Russia": "https://api.libreview.ru",
    "United States": "https://api-us.libreview.io",
}
PRODUCT = "llu.android"
VERSION_APP = "4.7"
GLUCOSE_VALUE_ICON = "mdi:diabetes"
GLUCOSE_TREND_ICON = {
    1: "mdi:arrow-down-bold-box",
    2: "mdi:arrow-bottom-right-bold-box",
    3: "mdi:arrow-right-bold-box",
    4: "mdi:arrow-top-right-bold-box",
    5: "mdi:arrow-up-bold-box",
}
GLUCOSE_TREND_MESSAGE = {
    1: "Decreasing fast",
    2: "Decreasing",
    3: "Stable",
    4: "Increasing",
    5: "Increasing fast",
}

REFRESH_RATE_MIN = 1
API_TIME_OUT_SECONDS = 20
