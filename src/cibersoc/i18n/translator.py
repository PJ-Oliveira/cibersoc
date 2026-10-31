from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
import json
from pathlib import Path


class SupportedLocale(StrEnum):
    ENGLISH_UK = "en-GB"
    PORTUGUESE = "pt"
    SPANISH = "es"


_CATALOGUE_FILENAMES: dict[SupportedLocale, str] = {
    SupportedLocale.ENGLISH_UK: "en_GB.json",
    SupportedLocale.PORTUGUESE: "pt.json",
    SupportedLocale.SPANISH: "es.json",
}


class LocalizationCatalog:
    def __init__(
        self,
        initial_locale: SupportedLocale = SupportedLocale.ENGLISH_UK,
        catalogue_directory: Path | None = None,
    ) -> None:
        base_directory = catalogue_directory or (Path(__file__).resolve().parent / "catalogues")
        self._catalogues: dict[SupportedLocale, dict[str, str]] = {}
        for locale, filename in _CATALOGUE_FILENAMES.items():
            file_path = base_directory / filename
            raw_mapping = json.loads(file_path.read_text(encoding="utf-8"))
            self._catalogues[locale] = {str(key): str(value) for key, value in raw_mapping.items()}

        self._verify_key_symmetry()
        self._active_locale: SupportedLocale = initial_locale
        self._listeners: list[Callable[[SupportedLocale], None]] = []

    def _verify_key_symmetry(self) -> None:
        reference_keys = set(self._catalogues[SupportedLocale.ENGLISH_UK].keys())
        for locale, mapping in self._catalogues.items():
            current_keys = set(mapping.keys())
            if current_keys != reference_keys:
                missing_keys = sorted(reference_keys - current_keys)
                surplus_keys = sorted(current_keys - reference_keys)
                raise ValueError(
                    f"Asymmetric translation catalogue for '{locale.value}': "
                    f"missing={missing_keys}, surplus={surplus_keys}"
                )

    @property
    def active_locale(self) -> SupportedLocale:
        return self._active_locale

    @property
    def available_keys(self) -> frozenset[str]:
        return frozenset(self._catalogues[SupportedLocale.ENGLISH_UK].keys())

    def switch_locale(self, target_locale: SupportedLocale) -> None:
        if target_locale == self._active_locale:
            return
        self._active_locale = target_locale
        for callback in list(self._listeners):
            callback(self._active_locale)

    def register_locale_listener(self, callback: Callable[[SupportedLocale], None]) -> None:
        self._listeners.append(callback)

    def translate(self, message_key: str, **parameters: object) -> str:
        active_mapping = self._catalogues[self._active_locale]
        if message_key not in active_mapping:
            raise KeyError(f"Unknown translation key: '{message_key}'")
        template = active_mapping[message_key]
        if not parameters:
            return template
        return template.format(**parameters)
