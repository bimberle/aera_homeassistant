"""Ayla Networks API Client for Aera Smart Diffusers."""

from .client import (
    AylaApi,
    AylaApiError,
    AylaAuthError,
    AylaAuthToken,
    AeraDevice as AeraDeviceBase,
)

from .aera import (
    AeraApi,
    AeraDevice,
    AeraDeviceState,
    AeraIntensity,
    AeraMode,
    AeraSessionDuration,
)

from .fragrances import (
    FRAGRANCES,
    FRAGRANCE_IDS,
    get_fragrance_name,
    get_fragrance_id,
    fetch_fragrances,
    clear_fragrance_cache,
)

__all__ = [
    # Low-level Ayla API
    "AylaApi",
    "AylaApiError",
    "AylaAuthError",
    "AylaAuthToken",
    # High-level Aera API
    "AeraApi",
    "AeraDevice",
    "AeraDeviceState",
    "AeraIntensity",
    "AeraMode",
    "AeraSessionDuration",
    # Fragrances
    "FRAGRANCES",
    "FRAGRANCE_IDS",
    "get_fragrance_name",
    "get_fragrance_id",
    "fetch_fragrances",
    "clear_fragrance_cache",
]
