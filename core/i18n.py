from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_LOCALE = "en"
_LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"


class TranslationError(RuntimeError):
    """Raised when translation resources are malformed."""


class LocalizationService:
    """Load and resolve GuildPet translations with English fallback."""

    def __init__(
        self,
        locale_dir: Path | str | None = None,
        *,
        default_locale: str = DEFAULT_LOCALE,
    ) -> None:
        self.locale_dir = Path(locale_dir) if locale_dir else _LOCALE_DIR
        self.default_locale = self.normalize_locale(default_locale)
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def normalize_locale(locale: str | None) -> str:
        if not locale:
            return DEFAULT_LOCALE
        normalized = str(locale).strip().replace("_", "-")
        if not normalized:
            return DEFAULT_LOCALE

        parts = normalized.split("-")
        language = parts[0].lower()
        if len(parts) == 1:
            return language
        region = parts[1].upper()
        return f"{language}-{region}"

    def available_languages(self) -> tuple[str, ...]:
        if not self.locale_dir.exists():
            return (self.default_locale,)
        locales = sorted(path.stem for path in self.locale_dir.glob("*.json"))
        if self.default_locale not in locales:
            locales.insert(0, self.default_locale)
        return tuple(dict.fromkeys(locales))

    def reload_locales(self) -> None:
        with self._lock:
            self._cache.clear()

    def load_locale(self, locale: str | None) -> dict[str, Any]:
        normalized = self.normalize_locale(locale)
        with self._lock:
            cached = self._cache.get(normalized)
            if cached is not None:
                return cached

            path = self.locale_dir / f"{normalized}.json"
            if not path.exists() and "-" in normalized:
                language_only = normalized.split("-", 1)[0]
                path = self.locale_dir / f"{language_only}.json"
                normalized = language_only

            if not path.exists():
                if normalized != self.default_locale:
                    return self.load_locale(self.default_locale)
                raise TranslationError(f"Missing default locale file: {path}")

            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise TranslationError(f"Could not load locale {normalized!r}: {exc}") from exc

            if not isinstance(payload, dict):
                raise TranslationError(f"Locale {normalized!r} must contain a JSON object")

            self._cache[normalized] = payload
            return payload

    @staticmethod
    def _lookup(payload: dict[str, Any], key: str) -> Any:
        current: Any = payload
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def translate(self, locale: str | None, key: str, **kwargs: Any) -> str:
        normalized = self.normalize_locale(locale)
        value = self._lookup(self.load_locale(normalized), key)

        if value is None and normalized != self.default_locale:
            value = self._lookup(self.load_locale(self.default_locale), key)

        if value is None:
            LOGGER.warning("Missing translation key %s for locale %s", key, normalized)
            return key

        if not isinstance(value, str):
            LOGGER.warning("Translation key %s is not a string", key)
            return key

        if not kwargs:
            return value

        try:
            return value.format_map(_SafeFormatDict(kwargs))
        except (ValueError, KeyError) as exc:
            LOGGER.warning("Could not format translation %s: %s", key, exc)
            return value


class _SafeFormatDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


_service = LocalizationService()


def load_locale(locale: str | None) -> dict[str, Any]:
    return _service.load_locale(locale)


def tr(locale: str | None, key: str, **kwargs: Any) -> str:
    return _service.translate(locale, key, **kwargs)


def available_languages() -> tuple[str, ...]:
    return _service.available_languages()


def locale_metadata(locale: str | None) -> dict[str, str]:
    normalized = _service.normalize_locale(locale)
    payload = _service.load_locale(normalized)
    meta = payload.get("meta", {})

    if not isinstance(meta, dict):
        return {
            "name": normalized,
            "native_name": normalized,
        }

    name = meta.get("name")
    native_name = meta.get("native_name")

    return {
        "name": name if isinstance(name, str) and name else normalized,
        "native_name": (
            native_name
            if isinstance(native_name, str) and native_name
            else normalized
        ),
    }


def language_choices() -> tuple[tuple[str, str], ...]:
    choices: list[tuple[str, str]] = []

    for locale in available_languages():
        meta = locale_metadata(locale)
        native_name = meta["native_name"]
        english_name = meta["name"]

        if native_name.casefold() == english_name.casefold():
            display_name = native_name
        else:
            display_name = f"{native_name} ({english_name})"

        choices.append((display_name[:100], locale))

    return tuple(choices)


def reload_locales() -> None:
    _service.reload_locales()
