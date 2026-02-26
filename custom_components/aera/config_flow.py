"""Config flow for Aera integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AeraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aera."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Import here to avoid loading at startup
            from .ayla_api import AeraApi

            api = AeraApi(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )

            try:
                await api.login()
                devices = await api.get_devices()
                await api.close()
            except Exception:
                _LOGGER.exception("Failed to connect to Aera")
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    # Use email as unique ID
                    await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Aera ({user_input[CONF_EMAIL]})",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
