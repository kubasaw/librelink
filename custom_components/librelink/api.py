"""I used the https://libreview-unofficial.stoplight.io/docs/libreview-unofficial/ as a starting point to use the Abbot Libreview API."""

from __future__ import annotations

import asyncio
import logging
import socket

import aiohttp

from .const import API_TIME_OUT_SECONDS, CONNECTION_URL, LOGIN_URL, PRODUCT, VERSION_APP

_LOGGER = logging.getLogger(__name__)


class LibreLinkAPIError(Exception):
    """Base class for exceptions in this module."""


class LibreLinkAPIAuthenticationError(LibreLinkAPIError):
    """Exception raised when the API authentication fails."""

    def __init__(self) -> None:
        """Initialize the API error."""
        super().__init__("Invalid credentials")


class LibreLinkAPIConnectionError(LibreLinkAPIError):
    """Exception raised when the API connection fails."""

    def __init__(self, message: str = None) -> None:
        """Initialize the API error."""
        super().__init__(message or "Connection error")


class LibreLinkAPI:
    """API class for communication with the LibreLink API."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._token = None
        self._session = session
        self.base_url = base_url

    async def async_get_data(self):
        """Get data from the API."""
        response = await self._call_api(url=CONNECTION_URL)
        _LOGGER.debug("Return API Status:%s ", response["status"])
        # API status return 0 if everything goes well.
        if response["status"] != 0:
            return response  # to be used for debugging in status not ok

        patients = sorted(response["data"], key=lambda x: x["patientId"])
        _LOGGER.debug(
            "Number of patients : %s and patient list %s", len(patients), patients
        )
        return patients

    async def async_login(self, username: str, password: str) -> str:
        """Get token from the API."""
        response = await self._call_api(
            url=LOGIN_URL,
            data={"email": username, "password": password},
            authenticated=False,
        )
        _LOGGER.debug("Login status : %s", response["status"])
        if response["status"] == 2:
            raise LibreLinkAPIAuthenticationError()
        self._token = response["data"]["authTicket"]["token"]

    async def _call_api(
        self,
        url: str,
        data: dict | None = None,
        authenticated: bool = True,
    ) -> any:
        """Get information from the API."""
        headers = {
            "product": PRODUCT,
            "version": VERSION_APP,
        }
        if authenticated:
            headers["Authorization"] = "Bearer " + self._token

        call_method = self._session.post if data else self._session.get
        try:
            async with asyncio.timeout(API_TIME_OUT_SECONDS):
                response = await call_method(
                    url=self.base_url + url, headers=headers, json=data
                )
                _LOGGER.debug("response.status: %s", response.status)
                if response.status in (401, 403):
                    raise LibreLinkAPIAuthenticationError()
                response.raise_for_status()
                return await response.json()
        except TimeoutError as e:
            raise LibreLinkAPIConnectionError("Timeout Error") from e
        except (aiohttp.ClientError, socket.gaierror) as e:
            raise LibreLinkAPIConnectionError() from e
        except Exception as e:
            raise LibreLinkAPIError() from e
