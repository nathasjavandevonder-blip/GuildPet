from pathlib import Path
import tempfile
import json

from core.i18n import LocalizationService


def test_translation_and_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "en.json").write_text(json.dumps({"hello": "Hello {name}"}), encoding="utf-8")
        (path / "nl.json").write_text(json.dumps({"hello": "Hallo {name}"}), encoding="utf-8")

        service = LocalizationService(path)
        assert service.translate("nl", "hello", name="Nathasja") == "Hallo Nathasja"
        assert service.translate("fr", "hello", name="Nathasja") == "Hello Nathasja"
        assert service.translate("nl", "missing.key") == "missing.key"


def test_locale_normalization() -> None:
    assert LocalizationService.normalize_locale("pt_br") == "pt-BR"
    assert LocalizationService.normalize_locale("NL") == "nl"
    assert LocalizationService.normalize_locale(None) == "en"
