import libs.langtable as langtable
import globals as GV

COMMON_LANGUAGES = langtable.list_common_languages()
ALL_LOCALES = langtable.list_all_locales()
#ALL_TIMEZONES = langtable.list_all_timezones()
ALL_KEYMAPS = langtable.list_all_keyboards()
#ALL_KEYMAPS_BY_DESC = {langtable._keyboards_db[key].description: key for key in ALL_KEYMAPS}


def all_timezones():
    """
    Get all timezones, but with the Etc zones reduced. Cached.
    :rtype: set
    """
    return langtable.list_all_timezones()


def get_available_keymaps():
    return ALL_KEYMAPS

'''
def get_available_keymaps_by_description():
    return ALL_KEYMAPS_BY_DESC

def get_keymap_by_description(keymap_description):
    return ALL_KEYMAPS_BY_DESC[keymap_description]
'''
def get_keymap_description(keymap):
    return langtable._keyboards_db[keymap].description

def is_valid_timezone(timezone):
    """
    Check if a given string is an existing timezone.
    :type timezone: str
    :rtype: bool
    """

    return timezone in all_timezones()


def get_timezone(timezone):
    """
    Return a tzinfo object for a given timezone name.
    :param str timezone: the timezone name
    :rtype: datetime.tzinfo
    """
    import zoneinfo
    return zoneinfo.ZoneInfo(timezone)


def get_xlated_timezone(tz_spec_part):
    """Function returning translated name of a region, city or complete timezone
    name according to the current value of the $LANG variable.
    :param tz_spec_part: a region, city or complete timezone name
    :type tz_spec_part: str
    :return: translated name of the given region, city or timezone
    :rtype: str
    :raise InvalidLocaleSpec: if an invalid locale is given (see is_valid_langcode)
    """

    xlated = langtable.timezone_name(tz_spec_part, languageIdQuery='en')
    return xlated


def get_locales_in_territory(territory):
    return langtable.list_locales(territoryId=territory)


def get_locales_in_language(lang):
    return langtable.list_locales(languageId=lang)


def get_language_in_locale(locale):
    return langtable.parse_locale(locale).language


def get_keymaps(lang=None, territory=None):
    keymaps_list = langtable.list_keyboards(territoryId=territory, languageId=lang)
    new_keymap_list = []
    for keymap in keymaps_list:
        #keymap = keymap.replace('(', ' (')
        new_keymap_list.append(keymap)
    return new_keymap_list


def get_lang_or_locale_native_and_en_name(lang_or_locale):
    lang_or_locale_native_name = langtable.language_name(languageId=lang_or_locale)
    lang_or_locale_english_name = langtable.language_name(languageId=lang_or_locale, languageIdQuery='en')
    return lang_or_locale_english_name, lang_or_locale_native_name, lang_or_locale


def check_valid_locale(locale):
    return locale in ALL_LOCALES


def get_locales_and_langs_sorted_with_names(territory=None):
    langs_id = []
    if territory:
        locales_in_territory = get_locales_in_territory(territory)
        for locale in locales_in_territory:
            if check_valid_locale(locale):
                lang_in_locale = get_language_in_locale(locale)
                if lang_in_locale not in langs_id:
                    langs_id.append(lang_in_locale)
    for lang in COMMON_LANGUAGES:
        if lang not in langs_id:
            langs_id.append(lang)
    for locale in ALL_LOCALES:
        lang_in_locale = get_language_in_locale(locale)
        if lang_in_locale not in langs_id:
            langs_id.append(lang_in_locale)
    langs_locales_sorted = []
    for lang_id in langs_id:
        all_lang_locales = get_locales_in_language(lang_id)
        supported_lang_locales = []
        for locale in all_lang_locales:
            if check_valid_locale(locale):
                supported_lang_locales.append(locale)
        if supported_lang_locales:
            langs_locales_sorted.append([lang_id, supported_lang_locales])
    for i in range(len(langs_locales_sorted)):
        langs_locales_sorted[i][0] = get_lang_or_locale_native_and_en_name(langs_locales_sorted[i][0])
        for j in range(len(langs_locales_sorted[i][1])):
            langs_locales_sorted[i][1][j] = get_lang_or_locale_native_and_en_name(langs_locales_sorted[i][1][j])
    return langs_locales_sorted

print(langtable._keyboards_db['de(nodeadkeys)'].description)
