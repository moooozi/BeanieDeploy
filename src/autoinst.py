from typing import Any

from services.patched_langtable import keyboards_db, langtable

COMMON_LANGUAGES = langtable.list_common_languages()
ALL_LOCALES = langtable.list_all_locales()
# ALL_TIMEZONES = langtable.list_all_timezones()
ALL_KEYMAPS = langtable.list_all_keyboards()
ALL_LANGUAGES = langtable.list_all_languages()
ALL_KEYMAPS_BY_DESC = {keyboards_db[key].description: key for key in ALL_KEYMAPS}
# fmt: off
SUPPORTED_LANGS = ['af', 'am', 'ar', 'as', 'ast', 'be', 'bg', 'bn', 'ca', 'cmn', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fil', 'fr', 'fur', 'fy', 'ga', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'ia', 'id', 'is', 'it', 'ja', 'ka', 'kab', 'kk', 'km', 'kn', 'ko', 'kw', 'lt', 'lv', 'ml', 'mr', 'my', 'nb', 'nl', 'nn', 'oc', 'or', 'pa', 'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sl', 'sq', 'sr', 'sv', 'ta', 'te', 'th', 'tr', 'uk', 'ur', 'vi']  # noqa: Q000
# fmt: on


def all_timezones() -> list[str]:
    """
    Get all timezones, but with the Etc zones reduced. Cached.
    :rtype: set
    """
    return langtable.list_all_timezones()


def get_available_keymaps() -> list[str]:
    return ALL_KEYMAPS


"""
def get_available_keymaps_by_description():
    return ALL_KEYMAPS_BY_DESC

def get_keymap_by_description(keymap_description):
    return ALL_KEYMAPS_BY_DESC[keymap_description]
"""


def get_keymap_description(keymap: str) -> str:
    return keyboards_db[keymap].description


def is_valid_timezone(timezone: str) -> bool:
    """
    Check if a given string is an existing timezone.
    :type timezone: str
    :rtype: bool
    """

    return timezone in all_timezones()


def get_timezone(timezone: str) -> Any:
    """
    Return a tzinfo object for a given timezone name.
    :param str timezone: the timezone name
    :rtype: datetime.tzinfo
    """
    import zoneinfo

    return zoneinfo.ZoneInfo(timezone)


def get_xlated_timezone(tz_spec_part: str) -> str:
    """Function returning translated name of a region, city or complete timezone
    name according to the current value of the $LANG variable.
    :param tz_spec_part: a region, city or complete timezone name
    :type tz_spec_part: str
    :return: translated name of the given region, city or timezone
    :rtype: str
    :raise InvalidLocaleSpec: if an invalid locale is given (see is_valid_langcode)
    """

    xlated = langtable.timezone_name(tz_spec_part, languageIdQuery="en")
    return xlated if xlated is not None else tz_spec_part


def get_locales_in_territory(territory: str) -> list[str]:
    return langtable.list_locales(concise=True, territoryId=territory)


def get_locales_in_language(lang: str) -> list[str]:
    return langtable.list_locales(concise=True, languageId=lang)


def get_language_in_locale(locale: str) -> str:
    return langtable.parse_locale(locale).language


def get_keymaps(lang: str | None = None, territory: str | None = None) -> list[str]:
    keymaps_list = langtable.list_keyboards(territoryId=territory, languageId=lang)
    new_keymap_list = []
    for keymap in keymaps_list:
        # keymap = keymap.replace('(', ' (')
        new_keymap_list.append(keymap)
    return new_keymap_list


def get_lang_or_locale_native_and_en_name(lang_or_locale: str) -> dict[str, str]:
    lang_or_locale_native_name = langtable.language_name(languageId=lang_or_locale)
    lang_or_locale_english_name = langtable.language_name(
        languageId=lang_or_locale, languageIdQuery="en"
    )
    return {
        "english": lang_or_locale_english_name,
        "native": lang_or_locale_native_name,
    }


def check_valid_locale(locale: str) -> bool:
    return locale in ALL_LOCALES


def get_locales_and_langs_sorted_with_names(
    locale_list: list | None = None,
) -> dict[str, Any]:
    langs_id = []
    if locale_list is None:
        locale_list = []
    if locale_list:
        for locale in locale_list:
            lang_in_locale = langtable.parse_locale(locale[0]).language
            if lang_in_locale not in ALL_LANGUAGES:
                continue
            if lang_in_locale not in langs_id:
                langs_id.append(lang_in_locale)
    for lang in COMMON_LANGUAGES:
        if lang not in langs_id:
            langs_id.append(lang)

    for lang in SUPPORTED_LANGS:
        if lang not in langs_id:
            langs_id.append(lang)

    langs_locales_sorted = {}
    for lang_id in langs_id:
        all_lang_locales = langtable.list_locales(concise=True, languageId=lang_id)
        supported_lang_locales = []
        for locale in all_lang_locales:
            if check_valid_locale(locale):
                supported_lang_locales.append(locale)
        if supported_lang_locales:
            langs_locales_sorted[lang_id] = {
                "locales": {
                    locale: {"names": get_lang_or_locale_native_and_en_name(locale)}
                    for locale in supported_lang_locales
                },
            }
    for lang_id in langs_locales_sorted:
        langs_locales_sorted[lang_id]["names"] = get_lang_or_locale_native_and_en_name(  # type: ignore
            lang_id
        )
    return langs_locales_sorted


def strip_encoding(locale_str):
    result = langtable.parse_locale(locale_str)
    parts = [result.language]
    if result.script:
        parts.append(result.script)
    if result.territory:
        parts.append(result.territory)
    if result.variant:
        parts.append(result.variant)
    return "_".join(parts)
