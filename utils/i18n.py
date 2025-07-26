import json
from pathlib import Path

class I18n:
    def __init__(self, locale_dir: str, default_lang: str = "ru"):
        self.locale_dir = Path(locale_dir)
        self.default_lang = default_lang
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        for file in self.locale_dir.glob("*.json"):
            lang_code = file.stem
            with open(file, "r", encoding="utf-8") as f:
                self.translations[lang_code] = json.load(f)

    def t(self, key: str, lang: str = None, **kwargs) -> str:
        lang = lang or self.default_lang
        template = self.translations.get(lang, {}).get(key) or self.translations[self.default_lang].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                return f"Missing placeholder: {e} in key: {key}"
        return template

i18n = I18n("locales")
