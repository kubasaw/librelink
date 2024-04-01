"""Adds config flow for LibreLink."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    LibreLinkAPI,
    LibreLinkAPIAuthenticationError,
    LibreLinkAPIConnectionError,
    LibreLinkAPIError,
)
from .const import BASE_URL_LIST, COUNTRY, COUNTRY_LIST, DOMAIN, LOGGER
from .units import UNITS_OF_MEASUREMENT

# GVS: Init logger
_LOGGER = logging.getLogger(__name__)


class LibreLinkFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for LibreLink."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                username = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]
                base_url = BASE_URL_LIST[user_input[COUNTRY]]

                client = LibreLinkAPI(
                    base_url=base_url, session=async_create_clientsession(self.hass)
                )
                await client.async_login(username, password)

                self.client = client

                return await self.async_step_patient()
            except LibreLinkAPIAuthenticationError as e:
                LOGGER.warning(e)
                _errors["base"] = "auth"
            except LibreLinkAPIConnectionError as e:
                LOGGER.error(e)
                _errors["base"] = "connection"
            except LibreLinkAPIError as e:
                LOGGER.exception(e)
                _errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                    vol.Required(
                        COUNTRY,
                        description="Country",
                        default=(COUNTRY_LIST[0]),
                    ): vol.In(COUNTRY_LIST),
                }
            ),
            errors=_errors,
        )

    async def async_step_patient(self, user_input=None):
        if user_input and "PATIENT_ID" in user_input:
            return self.async_create_entry(
                title=user_input[CONF_USERNAME],
                data=user_input,
            )

        data = await self.client.async_get_data()

        c1 = SelectSelectorConfig(
            options=[
                SelectOptionDict(
                    value=patient["patientId"],
                    label=f'{patient['firstName']} {patient["lastName"]}',
                )
                for patient in data
            ]
        )
        c2 = SelectSelectorConfig(
            options=[
                SelectOptionDict(value=k, label=u.unit_of_measurement)
                for k, u in UNITS_OF_MEASUREMENT.items()
            ]
        )

        return self.async_show_form(
            step_id="patient",
            data_schema=vol.Schema(
                {
                    vol.Required("PATIENT_ID"): SelectSelector(c1),
                    vol.Required(CONF_UNIT_OF_MEASUREMENT): SelectSelector(c2),
                }
            ),
        )
