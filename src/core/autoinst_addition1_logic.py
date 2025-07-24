"""
Business logic for PageAutoinstAddition1: language/locale selection and kickstart setup.
"""
import autoinst
from services.patched_langtable import langtable

def get_langs_and_locales(ip_locale):
    if ip_locale:
        return autoinst.get_locales_and_langs_sorted_with_names(territory=ip_locale["country_code"])
    return autoinst.get_locales_and_langs_sorted_with_names()

def get_fallback_langs_and_locales():
    return {
        "en": {
            "names": {"english": "English", "native": "English"},
            "locales": {"en_US.UTF-8": {"names": {"native": "English (United States)"}}}
        }
    }

def get_available_locales(ip_locale):
    if ip_locale:
        return langtable.list_locales(territoryId=ip_locale["country_code"])
    return []

def get_language_from_locale(locale):
    return autoinst.langtable.parse_locale(locale).language

def get_fallback_language(language, langs_and_locales):
    available_langs = list(langs_and_locales.keys())
    fallback_lang = next((lang for lang in available_langs if lang.startswith(language[:2])), None)
    if not fallback_lang and available_langs:
        fallback_lang = available_langs[0]
    return fallback_lang

def get_first_locale_for_language(langs_and_locales, language):
    if language in langs_and_locales and langs_and_locales[language]["locales"]:
        return list(langs_and_locales[language]["locales"].keys())[0]
    return None

def validate_locale(selected_locale):
    try:
        parsed = autoinst.langtable.parse_locale(selected_locale)
        if not parsed.language:
            return False, "Selected locale is invalid"
    except Exception as e:
        return False, f"Invalid locale format: {str(e)}"
    return True, None
