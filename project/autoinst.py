from libs import langtable

ETC_ZONES = ['GMT+1', 'GMT+2', 'GMT+3', 'GMT+4', 'GMT+5', 'GMT+6', 'GMT+7',
             'GMT+8', 'GMT+9', 'GMT+10', 'GMT+11', 'GMT+12',
             'GMT-1', 'GMT-2', 'GMT-3', 'GMT-4', 'GMT-5', 'GMT-6', 'GMT-7',
             'GMT-8', 'GMT-9', 'GMT-10', 'GMT-11', 'GMT-12', 'GMT-13',
             'GMT-14', 'UTC', 'GMT']

ALL_TIMEZONES = ['Africa/Abidjan', 'Africa/Accra', 'Africa/Addis_Ababa', 'Africa/Algiers', 'Africa/Asmara', 'Africa/Asmera', 'Africa/Bamako', 'Africa/Bangui', 'Africa/Banjul', 'Africa/Bissau', 'Africa/Blantyre', 'Africa/Brazzaville', 'Africa/Bujumbura', 'Africa/Cairo', 'Africa/Casablanca', 'Africa/Ceuta', 'Africa/Conakry', 'Africa/Dakar', 'Africa/Dar_es_Salaam', 'Africa/Djibouti', 'Africa/Douala', 'Africa/El_Aaiun', 'Africa/Freetown', 'Africa/Gaborone', 'Africa/Harare', 'Africa/Johannesburg', 'Africa/Juba', 'Africa/Kampala', 'Africa/Khartoum', 'Africa/Kigali', 'Africa/Kinshasa', 'Africa/Lagos', 'Africa/Libreville', 'Africa/Lome', 'Africa/Luanda', 'Africa/Lubumbashi', 'Africa/Lusaka', 'Africa/Malabo', 'Africa/Maputo', 'Africa/Maseru', 'Africa/Mbabane', 'Africa/Mogadishu', 'Africa/Monrovia', 'Africa/Nairobi', 'Africa/Ndjamena', 'Africa/Niamey', 'Africa/Nouakchott', 'Africa/Ouagadougou', 'Africa/Porto-Novo', 'Africa/Sao_Tome', 'Africa/Timbuktu', 'Africa/Tripoli', 'Africa/Tunis', 'Africa/Windhoek', 'America/Adak', 'America/Anchorage', 'America/Anguilla', 'America/Antigua', 'America/Araguaina', 'America/Argentina/Buenos_Aires', 'America/Argentina/Catamarca', 'America/Argentina/ComodRivadavia', 'America/Argentina/Cordoba', 'America/Argentina/Jujuy', 'America/Argentina/La_Rioja', 'America/Argentina/Mendoza', 'America/Argentina/Rio_Gallegos', 'America/Argentina/Salta', 'America/Argentina/San_Juan', 'America/Argentina/San_Luis', 'America/Argentina/Tucuman', 'America/Argentina/Ushuaia', 'America/Aruba', 'America/Asuncion', 'America/Atikokan', 'America/Atka', 'America/Bahia', 'America/Bahia_Banderas', 'America/Barbados', 'America/Belem', 'America/Belize', 'America/Blanc-Sablon', 'America/Boa_Vista', 'America/Bogota', 'America/Boise', 'America/Buenos_Aires', 'America/Cambridge_Bay', 'America/Campo_Grande', 'America/Cancun', 'America/Caracas', 'America/Catamarca', 'America/Cayenne', 'America/Cayman', 'America/Chicago', 'America/Chihuahua', 'America/Coral_Harbour', 'America/Cordoba', 'America/Costa_Rica', 'America/Creston', 'America/Cuiaba', 'America/Curacao', 'America/Danmarkshavn', 'America/Dawson', 'America/Dawson_Creek', 'America/Denver', 'America/Detroit', 'America/Dominica', 'America/Edmonton', 'America/Eirunepe', 'America/El_Salvador', 'America/Ensenada', 'America/Fort_Nelson', 'America/Fort_Wayne', 'America/Fortaleza', 'America/Glace_Bay', 'America/Godthab', 'America/Goose_Bay', 'America/Grand_Turk', 'America/Grenada', 'America/Guadeloupe', 'America/Guatemala', 'America/Guayaquil', 'America/Guyana', 'America/Halifax', 'America/Havana', 'America/Hermosillo', 'America/Indiana/Indianapolis', 'America/Indiana/Knox', 'America/Indiana/Marengo', 'America/Indiana/Petersburg', 'America/Indiana/Tell_City', 'America/Indiana/Vevay', 'America/Indiana/Vincennes', 'America/Indiana/Winamac', 'America/Indianapolis', 'America/Inuvik', 'America/Iqaluit', 'America/Jamaica', 'America/Jujuy', 'America/Juneau', 'America/Kentucky/Louisville', 'America/Kentucky/Monticello', 'America/Knox_IN', 'America/Kralendijk', 'America/La_Paz', 'America/Lima', 'America/Los_Angeles', 'America/Louisville', 'America/Lower_Princes', 'America/Maceio', 'America/Managua', 'America/Manaus', 'America/Marigot', 'America/Martinique', 'America/Matamoros', 'America/Mazatlan', 'America/Mendoza', 'America/Menominee', 'America/Merida', 'America/Metlakatla', 'America/Mexico_City', 'America/Miquelon', 'America/Moncton', 'America/Monterrey', 'America/Montevideo', 'America/Montreal', 'America/Montserrat', 'America/Nassau', 'America/New_York', 'America/Nipigon', 'America/Nome', 'America/Noronha', 'America/North_Dakota/Beulah', 'America/North_Dakota/Center', 'America/North_Dakota/New_Salem', 'America/Nuuk', 'America/Ojinaga', 'America/Panama', 'America/Pangnirtung', 'America/Paramaribo', 'America/Phoenix', 'America/Port-au-Prince', 'America/Port_of_Spain', 'America/Porto_Acre', 'America/Porto_Velho', 'America/Puerto_Rico', 'America/Punta_Arenas', 'America/Rainy_River', 'America/Rankin_Inlet', 'America/Recife', 'America/Regina', 'America/Resolute', 'America/Rio_Branco', 'America/Rosario', 'America/Santa_Isabel', 'America/Santarem', 'America/Santiago', 'America/Santo_Domingo', 'America/Sao_Paulo', 'America/Scoresbysund', 'America/Shiprock', 'America/Sitka', 'America/St_Barthelemy', 'America/St_Johns', 'America/St_Kitts', 'America/St_Lucia', 'America/St_Thomas', 'America/St_Vincent', 'America/Swift_Current', 'America/Tegucigalpa', 'America/Thule', 'America/Thunder_Bay', 'America/Tijuana', 'America/Toronto', 'America/Tortola', 'America/Vancouver', 'America/Virgin', 'America/Whitehorse', 'America/Winnipeg', 'America/Yakutat', 'America/Yellowknife', 'Antarctica/Casey', 'Antarctica/Davis', 'Antarctica/DumontDUrville', 'Antarctica/Macquarie', 'Antarctica/Mawson', 'Antarctica/McMurdo', 'Antarctica/Palmer', 'Antarctica/Rothera', 'Antarctica/South_Pole', 'Antarctica/Syowa', 'Antarctica/Troll', 'Antarctica/Vostok', 'Arctic/Longyearbyen', 'Asia/Aden', 'Asia/Almaty', 'Asia/Amman', 'Asia/Anadyr', 'Asia/Aqtau', 'Asia/Aqtobe', 'Asia/Ashgabat', 'Asia/Ashkhabad', 'Asia/Atyrau', 'Asia/Baghdad', 'Asia/Bahrain', 'Asia/Baku', 'Asia/Bangkok', 'Asia/Barnaul', 'Asia/Beirut', 'Asia/Bishkek', 'Asia/Brunei', 'Asia/Calcutta', 'Asia/Chita', 'Asia/Choibalsan', 'Asia/Chongqing', 'Asia/Chungking', 'Asia/Colombo', 'Asia/Dacca', 'Asia/Damascus', 'Asia/Dhaka', 'Asia/Dili', 'Asia/Dubai', 'Asia/Dushanbe', 'Asia/Famagusta', 'Asia/Gaza', 'Asia/Harbin', 'Asia/Hebron', 'Asia/Ho_Chi_Minh', 'Asia/Hong_Kong', 'Asia/Hovd', 'Asia/Irkutsk', 'Asia/Istanbul', 'Asia/Jakarta', 'Asia/Jayapura', 'Asia/Jerusalem', 'Asia/Kabul', 'Asia/Kamchatka', 'Asia/Karachi', 'Asia/Kashgar', 'Asia/Kathmandu', 'Asia/Katmandu', 'Asia/Khandyga', 'Asia/Kolkata', 'Asia/Krasnoyarsk', 'Asia/Kuala_Lumpur', 'Asia/Kuching', 'Asia/Kuwait', 'Asia/Macao', 'Asia/Macau', 'Asia/Magadan', 'Asia/Makassar', 'Asia/Manila', 'Asia/Muscat', 'Asia/Nicosia', 'Asia/Novokuznetsk', 'Asia/Novosibirsk', 'Asia/Omsk', 'Asia/Oral', 'Asia/Phnom_Penh', 'Asia/Pontianak', 'Asia/Pyongyang', 'Asia/Qatar', 'Asia/Qostanay', 'Asia/Qyzylorda', 'Asia/Rangoon', 'Asia/Riyadh', 'Asia/Saigon', 'Asia/Sakhalin', 'Asia/Samarkand', 'Asia/Seoul', 'Asia/Shanghai', 'Asia/Singapore', 'Asia/Srednekolymsk', 'Asia/Taipei', 'Asia/Tashkent', 'Asia/Tbilisi', 'Asia/Tehran', 'Asia/Tel_Aviv', 'Asia/Thimbu', 'Asia/Thimphu', 'Asia/Tokyo', 'Asia/Tomsk', 'Asia/Ujung_Pandang', 'Asia/Ulaanbaatar', 'Asia/Ulan_Bator', 'Asia/Urumqi', 'Asia/Ust-Nera', 'Asia/Vientiane', 'Asia/Vladivostok', 'Asia/Yakutsk', 'Asia/Yangon', 'Asia/Yekaterinburg', 'Asia/Yerevan', 'Atlantic/Azores', 'Atlantic/Bermuda', 'Atlantic/Canary', 'Atlantic/Cape_Verde', 'Atlantic/Faeroe', 'Atlantic/Faroe', 'Atlantic/Jan_Mayen', 'Atlantic/Madeira', 'Atlantic/Reykjavik', 'Atlantic/South_Georgia', 'Atlantic/St_Helena', 'Atlantic/Stanley', 'Australia/ACT', 'Australia/Adelaide', 'Australia/Brisbane', 'Australia/Broken_Hill', 'Australia/Canberra', 'Australia/Currie', 'Australia/Darwin', 'Australia/Eucla', 'Australia/Hobart', 'Australia/LHI', 'Australia/Lindeman', 'Australia/Lord_Howe', 'Australia/Melbourne', 'Australia/NSW', 'Australia/North', 'Australia/Perth', 'Australia/Queensland', 'Australia/South', 'Australia/Sydney', 'Australia/Tasmania', 'Australia/Victoria', 'Australia/West', 'Australia/Yancowinna', 'Brazil/Acre', 'Brazil/DeNoronha', 'Brazil/East', 'Brazil/West', 'CET', 'CST6CDT', 'Canada/Atlantic', 'Canada/Central', 'Canada/Eastern', 'Canada/Mountain', 'Canada/Newfoundland', 'Canada/Pacific', 'Canada/Saskatchewan', 'Canada/Yukon', 'Chile/Continental', 'Chile/EasterIsland', 'Cuba', 'EET', 'EST', 'EST5EDT', 'Egypt', 'Eire', 'Etc/GMT', 'Etc/GMT+0', 'Etc/GMT+1', 'Etc/GMT+10', 'Etc/GMT+11', 'Etc/GMT+12', 'Etc/GMT+2', 'Etc/GMT+3', 'Etc/GMT+4', 'Etc/GMT+5', 'Etc/GMT+6', 'Etc/GMT+7', 'Etc/GMT+8', 'Etc/GMT+9', 'Etc/GMT-0', 'Etc/GMT-1', 'Etc/GMT-10', 'Etc/GMT-11', 'Etc/GMT-12', 'Etc/GMT-13', 'Etc/GMT-14', 'Etc/GMT-2', 'Etc/GMT-3', 'Etc/GMT-4', 'Etc/GMT-5', 'Etc/GMT-6', 'Etc/GMT-7', 'Etc/GMT-8', 'Etc/GMT-9', 'Etc/GMT0', 'Etc/Greenwich', 'Etc/UCT', 'Etc/UTC', 'Etc/Universal', 'Etc/Zulu', 'Europe/Amsterdam', 'Europe/Andorra', 'Europe/Astrakhan', 'Europe/Athens', 'Europe/Belfast', 'Europe/Belgrade', 'Europe/Berlin', 'Europe/Bratislava', 'Europe/Brussels', 'Europe/Bucharest', 'Europe/Budapest', 'Europe/Busingen', 'Europe/Chisinau', 'Europe/Copenhagen', 'Europe/Dublin', 'Europe/Gibraltar', 'Europe/Guernsey', 'Europe/Helsinki', 'Europe/Isle_of_Man', 'Europe/Istanbul', 'Europe/Jersey', 'Europe/Kaliningrad', 'Europe/Kiev', 'Europe/Kirov', 'Europe/Lisbon', 'Europe/Ljubljana', 'Europe/London', 'Europe/Luxembourg', 'Europe/Madrid', 'Europe/Malta', 'Europe/Mariehamn', 'Europe/Minsk', 'Europe/Monaco', 'Europe/Moscow', 'Europe/Nicosia', 'Europe/Oslo', 'Europe/Paris', 'Europe/Podgorica', 'Europe/Prague', 'Europe/Riga', 'Europe/Rome', 'Europe/Samara', 'Europe/San_Marino', 'Europe/Sarajevo', 'Europe/Saratov', 'Europe/Simferopol', 'Europe/Skopje', 'Europe/Sofia', 'Europe/Stockholm', 'Europe/Tallinn', 'Europe/Tirane', 'Europe/Tiraspol', 'Europe/Ulyanovsk', 'Europe/Uzhgorod', 'Europe/Vaduz', 'Europe/Vatican', 'Europe/Vienna', 'Europe/Vilnius', 'Europe/Volgograd', 'Europe/Warsaw', 'Europe/Zagreb', 'Europe/Zaporozhye', 'Europe/Zurich', 'Factory', 'GB', 'GB-Eire', 'GMT', 'GMT+0', 'GMT-0', 'GMT0', 'Greenwich', 'HST', 'Hongkong', 'Iceland', 'Indian/Antananarivo', 'Indian/Chagos', 'Indian/Christmas', 'Indian/Cocos', 'Indian/Comoro', 'Indian/Kerguelen', 'Indian/Mahe', 'Indian/Maldives', 'Indian/Mauritius', 'Indian/Mayotte', 'Indian/Reunion', 'Iran', 'Israel', 'Jamaica', 'Japan', 'Kwajalein', 'Libya', 'MET', 'MST', 'MST7MDT', 'Mexico/BajaNorte', 'Mexico/BajaSur', 'Mexico/General', 'NZ', 'NZ-CHAT', 'Navajo', 'PRC', 'PST8PDT', 'Pacific/Apia', 'Pacific/Auckland', 'Pacific/Bougainville', 'Pacific/Chatham', 'Pacific/Chuuk', 'Pacific/Easter', 'Pacific/Efate', 'Pacific/Enderbury', 'Pacific/Fakaofo', 'Pacific/Fiji', 'Pacific/Funafuti', 'Pacific/Galapagos', 'Pacific/Gambier', 'Pacific/Guadalcanal', 'Pacific/Guam', 'Pacific/Honolulu', 'Pacific/Johnston', 'Pacific/Kanton', 'Pacific/Kiritimati', 'Pacific/Kosrae', 'Pacific/Kwajalein', 'Pacific/Majuro', 'Pacific/Marquesas', 'Pacific/Midway', 'Pacific/Nauru', 'Pacific/Niue', 'Pacific/Norfolk', 'Pacific/Noumea', 'Pacific/Pago_Pago', 'Pacific/Palau', 'Pacific/Pitcairn', 'Pacific/Pohnpei', 'Pacific/Ponape', 'Pacific/Port_Moresby', 'Pacific/Rarotonga', 'Pacific/Saipan', 'Pacific/Samoa', 'Pacific/Tahiti', 'Pacific/Tarawa', 'Pacific/Tongatapu', 'Pacific/Truk', 'Pacific/Wake', 'Pacific/Wallis', 'Pacific/Yap', 'Poland', 'Portugal', 'ROC', 'ROK', 'Singapore', 'Turkey', 'UCT', 'US/Alaska', 'US/Aleutian', 'US/Arizona', 'US/Central', 'US/East-Indiana', 'US/Eastern', 'US/Hawaii', 'US/Indiana-Starke', 'US/Michigan', 'US/Mountain', 'US/Pacific', 'US/Samoa', 'UTC', 'Universal', 'W-SU', 'WET', 'Zulu']

ALL_LOCALES = ['C.UTF-8', 'aa_DJ.UTF-8', 'aa_ER.UTF-8', 'aa_ER.UTF-8@saaho', 'aa_ET.UTF-8', 'af_ZA.UTF-8', 'agr_PE.UTF-8', 'ak_GH.UTF-8', 'am_ET.UTF-8', 'an_ES.UTF-8', 'anp_IN.UTF-8', 'ar_AE.UTF-8', 'ar_BH.UTF-8', 'ar_DZ.UTF-8', 'ar_EG.UTF-8', 'ar_IN.UTF-8', 'ar_IQ.UTF-8', 'ar_JO.UTF-8', 'ar_KW.UTF-8', 'ar_LB.UTF-8', 'ar_LY.UTF-8', 'ar_MA.UTF-8', 'ar_OM.UTF-8', 'ar_QA.UTF-8', 'ar_SA.UTF-8', 'ar_SD.UTF-8', 'ar_SS.UTF-8', 'ar_SY.UTF-8', 'ar_TN.UTF-8', 'ar_YE.UTF-8', 'as_IN.UTF-8', 'ast_ES.UTF-8', 'ayc_PE.UTF-8', 'az_AZ.UTF-8', 'az_IR.UTF-8', 'be_BY.UTF-8', 'be_BY.UTF-8@latin', 'bem_ZM.UTF-8', 'ber_DZ.UTF-8', 'ber_MA.UTF-8', 'bg_BG.UTF-8', 'bhb_IN.UTF-8', 'bho_IN.UTF-8', 'bho_NP.UTF-8', 'bi_VU.UTF-8', 'bn_BD.UTF-8', 'bn_IN.UTF-8', 'bo_CN.UTF-8', 'bo_IN.UTF-8', 'br_FR.UTF-8', 'brx_IN.UTF-8', 'bs_BA.UTF-8', 'byn_ER.UTF-8', 'ca_AD.UTF-8', 'ca_ES.UTF-8', 'ca_ES.UTF-8@valencia', 'ca_FR.UTF-8', 'ca_IT.UTF-8', 'ce_RU.UTF-8', 'chr_US.UTF-8', 'ckb_IQ.UTF-8', 'cmn_TW.UTF-8', 'crh_UA.UTF-8', 'cs_CZ.UTF-8', 'csb_PL.UTF-8', 'cv_RU.UTF-8', 'cy_GB.UTF-8', 'da_DK.UTF-8', 'de_AT.UTF-8', 'de_BE.UTF-8', 'de_CH.UTF-8', 'de_DE.UTF-8', 'de_IT.UTF-8', 'de_LI.UTF-8', 'de_LU.UTF-8', 'doi_IN.UTF-8', 'dsb_DE.UTF-8', 'dv_MV.UTF-8', 'dz_BT.UTF-8', 'el_CY.UTF-8', 'el_GR.UTF-8', 'en_AG.UTF-8', 'en_AU.UTF-8', 'en_BW.UTF-8', 'en_CA.UTF-8', 'en_DK.UTF-8', 'en_GB.UTF-8', 'en_HK.UTF-8', 'en_IE.UTF-8', 'en_IL.UTF-8', 'en_IN.UTF-8', 'en_NG.UTF-8', 'en_NZ.UTF-8', 'en_PH.UTF-8', 'en_SC.UTF-8', 'en_SG.UTF-8', 'en_US.UTF-8', 'en_ZA.UTF-8', 'en_ZM.UTF-8', 'en_ZW.UTF-8', 'eo.UTF-8', 'es_AR.UTF-8', 'es_BO.UTF-8', 'es_CL.UTF-8', 'es_CO.UTF-8', 'es_CR.UTF-8', 'es_CU.UTF-8', 'es_DO.UTF-8', 'es_EC.UTF-8', 'es_ES.UTF-8', 'es_GT.UTF-8', 'es_HN.UTF-8', 'es_MX.UTF-8', 'es_NI.UTF-8', 'es_PA.UTF-8', 'es_PE.UTF-8', 'es_PR.UTF-8', 'es_PY.UTF-8', 'es_SV.UTF-8', 'es_US.UTF-8', 'es_UY.UTF-8', 'es_VE.UTF-8', 'et_EE.UTF-8', 'eu_ES.UTF-8', 'fa_IR.UTF-8', 'ff_SN.UTF-8', 'fi_FI.UTF-8', 'fil_PH.UTF-8', 'fo_FO.UTF-8', 'fr_BE.UTF-8', 'fr_CA.UTF-8', 'fr_CH.UTF-8', 'fr_FR.UTF-8', 'fr_LU.UTF-8', 'fur_IT.UTF-8', 'fy_DE.UTF-8', 'fy_NL.UTF-8', 'ga_IE.UTF-8', 'gd_GB.UTF-8', 'gez_ER.UTF-8', 'gez_ER.UTF-8@abegede', 'gez_ET.UTF-8', 'gez_ET.UTF-8@abegede', 'gl_ES.UTF-8', 'gu_IN.UTF-8', 'gv_GB.UTF-8', 'ha_NG.UTF-8', 'hak_TW.UTF-8', 'he_IL.UTF-8', 'hi_IN.UTF-8', 'hif_FJ.UTF-8', 'hne_IN.UTF-8', 'hr_HR.UTF-8', 'hsb_DE.UTF-8', 'ht_HT.UTF-8', 'hu_HU.UTF-8', 'hy_AM.UTF-8', 'ia_FR.UTF-8', 'id_ID.UTF-8', 'ig_NG.UTF-8', 'ik_CA.UTF-8', 'is_IS.UTF-8', 'it_CH.UTF-8', 'it_IT.UTF-8', 'iu_CA.UTF-8', 'ja_JP.UTF-8', 'ka_GE.UTF-8', 'kab_DZ.UTF-8', 'kk_KZ.UTF-8', 'kl_GL.UTF-8', 'km_KH.UTF-8', 'kn_IN.UTF-8', 'ko_KR.UTF-8', 'kok_IN.UTF-8', 'ks_IN.UTF-8', 'ks_IN.UTF-8@devanagari', 'ku_TR.UTF-8', 'kw_GB.UTF-8', 'ky_KG.UTF-8', 'lb_LU.UTF-8', 'lg_UG.UTF-8', 'li_BE.UTF-8', 'li_NL.UTF-8', 'lij_IT.UTF-8', 'ln_CD.UTF-8', 'lo_LA.UTF-8', 'lt_LT.UTF-8', 'lv_LV.UTF-8', 'lzh_TW.UTF-8', 'mag_IN.UTF-8', 'mai_IN.UTF-8', 'mai_NP.UTF-8', 'mfe_MU.UTF-8', 'mg_MG.UTF-8', 'mhr_RU.UTF-8', 'mi_NZ.UTF-8', 'miq_NI.UTF-8', 'mjw_IN.UTF-8', 'mk_MK.UTF-8', 'ml_IN.UTF-8', 'mn_MN.UTF-8', 'mni_IN.UTF-8', 'mnw_MM.UTF-8', 'mr_IN.UTF-8', 'ms_MY.UTF-8', 'mt_MT.UTF-8', 'my_MM.UTF-8', 'nan_TW.UTF-8', 'nan_TW.UTF-8@latin', 'nb_NO.UTF-8', 'nds_DE.UTF-8', 'nds_NL.UTF-8', 'ne_NP.UTF-8', 'nhn_MX.UTF-8', 'niu_NU.UTF-8', 'niu_NZ.UTF-8', 'nl_AW.UTF-8', 'nl_BE.UTF-8', 'nl_NL.UTF-8', 'nn_NO.UTF-8', 'nr_ZA.UTF-8', 'nso_ZA.UTF-8', 'oc_FR.UTF-8', 'om_ET.UTF-8', 'om_KE.UTF-8', 'or_IN.UTF-8', 'os_RU.UTF-8', 'pa_IN.UTF-8', 'pa_PK.UTF-8', 'pap_AW.UTF-8', 'pap_CW.UTF-8', 'pl_PL.UTF-8', 'ps_AF.UTF-8', 'pt_BR.UTF-8', 'pt_PT.UTF-8', 'quz_PE.UTF-8', 'raj_IN.UTF-8', 'ro_RO.UTF-8', 'ru_RU.UTF-8', 'ru_UA.UTF-8', 'rw_RW.UTF-8', 'sa_IN.UTF-8', 'sah_RU.UTF-8', 'sat_IN.UTF-8', 'sc_IT.UTF-8', 'sd_IN.UTF-8', 'sd_IN.UTF-8@devanagari', 'se_NO.UTF-8', 'sgs_LT.UTF-8', 'shn_MM.UTF-8', 'shs_CA.UTF-8', 'si_LK.UTF-8', 'sid_ET.UTF-8', 'sk_SK.UTF-8', 'sl_SI.UTF-8', 'sm_WS.UTF-8', 'so_DJ.UTF-8', 'so_ET.UTF-8', 'so_KE.UTF-8', 'so_SO.UTF-8', 'sq_AL.UTF-8', 'sq_MK.UTF-8', 'sr_ME.UTF-8', 'sr_RS.UTF-8', 'sr_RS.UTF-8@latin', 'ss_ZA.UTF-8', 'st_ZA.UTF-8', 'sv_FI.UTF-8', 'sv_SE.UTF-8', 'sw_KE.UTF-8', 'sw_TZ.UTF-8', 'szl_PL.UTF-8', 'ta_IN.UTF-8', 'ta_LK.UTF-8', 'tcy_IN.UTF-8', 'te_IN.UTF-8', 'tg_TJ.UTF-8', 'th_TH.UTF-8', 'the_NP.UTF-8', 'ti_ER.UTF-8', 'ti_ET.UTF-8', 'tig_ER.UTF-8', 'tk_TM.UTF-8', 'tl_PH.UTF-8', 'tn_ZA.UTF-8', 'to_TO.UTF-8', 'tpi_PG.UTF-8', 'tr_CY.UTF-8', 'tr_TR.UTF-8', 'ts_ZA.UTF-8', 'tt_RU.UTF-8', 'tt_RU.UTF-8@iqtelif', 'ug_CN.UTF-8', 'uk_UA.UTF-8', 'unm_US.UTF-8', 'ur_IN.UTF-8', 'ur_PK.UTF-8', 'uz_UZ.UTF-8', 'uz_UZ.UTF-8@cyrillic', 've_ZA.UTF-8', 'vi_VN.UTF-8', 'wa_BE.UTF-8', 'wae_CH.UTF-8', 'wal_ET.UTF-8', 'wo_SN.UTF-8', 'xh_ZA.UTF-8', 'yi_US.UTF-8', 'yo_NG.UTF-8', 'yue_HK.UTF-8', 'yuw_PG.UTF-8', 'zh_CN.UTF-8', 'zh_HK.UTF-8', 'zh_SG.UTF-8', 'zh_TW.UTF-8', 'zu_ZA.UTF-8']

COMMON_LANGUAGES = langtable.list_common_languages()

ALL_KEYMAPS = ['al', 'al-plisi', 'at', 'at-mac', 'at-nodeadkeys', 'az', 'ba', 'ba-alternatequotes', 'ba-unicode',
               'ba-unicodeus', 'ba-us', 'be', 'be-iso-alternate', 'be-nodeadkeys', 'be-oss', 'be-oss_latin9', 'be-wang',
               'br', 'br-dvorak', 'br-nativo', 'br-nativo-epo', 'br-nativo-us', 'br-nodeadkeys', 'br-thinkpad',
               'by-latin', 'ca', 'ca-eng', 'ca-fr-dvorak', 'ca-fr-legacy', 'ca-multi', 'ca-multix', 'ch', 'ch-de_mac',
               'ch-de_nodeadkeys', 'ch-fr', 'ch-fr_mac', 'ch-fr_nodeadkeys', 'ch-legacy', 'cm', 'cm-azerty', 'cm-dvorak',
               'cm-french', 'cm-mmuock', 'cm-qwerty', 'cn', 'cn-altgr-pinyin', 'cz', 'cz-bksl', 'cz-dvorak-ucw', 'cz-qwerty',
               'cz-qwerty-mac', 'cz-qwerty_bksl', 'cz-rus', 'de', 'de-T3', 'de-deadacute', 'de-deadgraveacute', 'de-deadtilde',
               'de-dsb', 'de-dsb_qwertz', 'de-dvorak', 'de-e1', 'de-e2', 'de-mac', 'de-mac_nodeadkeys', 'de-neo',
               'de-nodeadkeys', 'de-qwerty', 'de-ro', 'de-ro_nodeadkeys', 'de-tr', 'de-us', 'dk', 'dk-dvorak', 'dk-mac',
               'dk-mac_nodeadkeys', 'dk-nodeadkeys', 'dk-winkeys', 'dz', 'dz-azerty-deadkeys', 'dz-qwerty-gb-deadkeys',
               'dz-qwerty-us-deadkeys', 'ee', 'ee-dvorak', 'ee-nodeadkeys', 'ee-us', 'epo', 'epo-legacy', 'es', 'es-ast',
               'es-cat', 'es-deadtilde', 'es-dvorak', 'es-mac', 'es-nodeadkeys', 'es-winkeys', 'fi', 'fi-classic', 'fi-mac',
               'fi-nodeadkeys', 'fi-smi', 'fi-winkeys', 'fo', 'fo-nodeadkeys', 'fr', 'fr-afnor', 'fr-azerty', 'fr-bepo',
               'fr-bepo_afnor', 'fr-bepo_latin9', 'fr-bre', 'fr-dvorak', 'fr-latin9', 'fr-latin9_nodeadkeys', 'fr-mac',
               'fr-nodeadkeys', 'fr-oci', 'fr-oss', 'fr-oss_latin9', 'fr-oss_nodeadkeys', 'fr-us', 'gb', 'gb-colemak',
               'gb-colemak_dh', 'gb-dvorak', 'gb-dvorakukp', 'gb-extd', 'gb-intl', 'gb-mac', 'gb-mac_intl', 'gb-pl', 'ge',
               'ge-ergonomic', 'ge-mess', 'ge-ru', 'gh', 'gh-akan', 'gh-avn', 'gh-ewe', 'gh-fula', 'gh-ga', 'gh-generic',
               'gh-gillbt', 'gh-hausa', 'hr', 'hr-alternatequotes', 'hr-unicode', 'hr-unicodeus', 'hr-us', 'hu',
               'hu-101_qwerty_comma_dead', 'hu-101_qwerty_comma_nodead', 'hu-101_qwerty_dot_dead', 'hu-101_qwerty_dot_nodead',
               'hu-101_qwertz_comma_dead', 'hu-101_qwertz_comma_nodead', 'hu-101_qwertz_dot_dead', 'hu-101_qwertz_dot_nodead',
               'hu-102_qwerty_comma_dead', 'hu-102_qwerty_comma_nodead', 'hu-102_qwerty_dot_dead', 'hu-102_qwerty_dot_nodead',
               'hu-102_qwertz_comma_dead', 'hu-102_qwertz_comma_nodead', 'hu-102_qwertz_dot_dead', 'hu-102_qwertz_dot_nodead',
               'hu-nodeadkeys', 'hu-qwerty', 'hu-standard', 'id', 'ie', 'ie-CloGaelach', 'ie-UnicodeExpert', 'ie-ogam_is434',
               'il', 'in-eng', 'in-iipa', 'iq-ku', 'iq-ku_alt', 'iq-ku_ara', 'iq-ku_f', 'ir-ku', 'ir-ku_alt', 'ir-ku_ara',
               'ir-ku_f', 'is', 'is-dvorak', 'is-mac', 'is-mac_legacy', 'it', 'it-fur', 'it-geo', 'it-ibm', 'it-intl', 'it-mac',
               'it-nodeadkeys', 'it-scn', 'it-us', 'it-winkeys', 'jp', 'jp-OADG109A', 'jp-dvorak', 'jp-kana86', 'ke', 'ke-kik',
               'kr', 'kr-kr104', 'kz-latin', 'latam', 'latam-colemak', 'latam-colemak-gaming', 'latam-deadtilde', 'latam-dvorak',
               'latam-nodeadkeys', 'lk-us', 'lt', 'lt-ibm', 'lt-lekp', 'lt-lekpa', 'lt-ratise', 'lt-sgs', 'lt-std', 'lt-us', 'lv',
               'lv-adapted', 'lv-apostrophe', 'lv-ergonomic', 'lv-fkey', 'lv-modern', 'lv-tilde', 'ma-french', 'md', 'md-gag', 'me',
               'me-latinalternatequotes', 'me-latinunicode', 'me-latinunicodeyz', 'me-latinyz', 'ml', 'ml-fr-oss', 'ml-us-intl',
               'ml-us-mac', 'mm', 'mt', 'mt-alt-gb', 'mt-alt-us', 'mt-us', 'ng', 'ng-hausa', 'ng-igbo', 'ng-yoruba', 'nl', 'nl-mac',
               'nl-std', 'nl-us', 'no', 'no-colemak', 'no-dvorak', 'no-mac', 'no-mac_nodeadkeys', 'no-nodeadkeys', 'no-smi',
               'no-smi_nodeadkeys', 'no-winkeys', 'ph', 'ph-capewell-dvorak', 'ph-capewell-qwerf2k6', 'ph-colemak', 'ph-dvorak',
               'pl', 'pl-csb', 'pl-dvorak', 'pl-dvorak_altquotes', 'pl-dvorak_quotes', 'pl-dvp', 'pl-legacy', 'pl-qwertz', 'pl-szl',
               'pt', 'pt-mac', 'pt-mac_nodeadkeys', 'pt-nativo', 'pt-nativo-epo', 'pt-nativo-us', 'pt-nodeadkeys', 'ro', 'ro-std',
               'ro-winkeys', 'rs-latin', 'rs-latinalternatequotes', 'rs-latinunicode', 'rs-latinunicodeyz', 'rs-latinyz', 'ru-cv_latin',
               'se', 'se-dvorak', 'se-mac', 'se-nodeadkeys', 'se-smi', 'se-svdvorak', 'se-us', 'se-us_dvorak', 'si', 'si-alternatequotes',
               'si-us', 'sk', 'sk-bksl', 'sk-qwerty', 'sk-qwerty_bksl', 'sy-ku', 'sy-ku_alt', 'sy-ku_f', 'tm', 'tm-alt', 'tr', 'tr-alt',
               'tr-crh', 'tr-crh_alt', 'tr-crh_f', 'tr-f', 'tr-intl', 'tr-ku', 'tr-ku_alt', 'tr-ku_f', 'tw', 'tw-indigenous',
               'tw-saisiyat', 'us', 'us-alt-intl', 'us-altgr-intl', 'us-colemak', 'us-colemak_dh', 'us-colemak_dh_iso', 'us-dvorak',
               'us-dvorak-alt-intl', 'us-dvorak-classic', 'us-dvorak-intl', 'us-dvorak-l', 'us-dvorak-mac', 'us-dvorak-r', 'us-dvp',
               'us-euro', 'us-haw', 'us-hbs', 'us-intl', 'us-mac', 'us-norman', 'us-olpc2', 'us-symbolic', 'us-workman', 'us-workman-intl',
               'uz-latin', 'vn', 'vn-fr', 'vn-us']


def all_timezones():
    """
    Get all timezones, but with the Etc zones reduced. Cached.
    :rtype: set
    """
    return ALL_TIMEZONES


'''
def get_all_regions_and_timezones():
    """
    Get a dictionary mapping the regions to the list of their timezones.
    :rtype: dict
    """

    result = OrderedDict()

    for tz in sorted(all_timezones()):
        parts = tz.split("/", 1)

        if len(parts) > 1:
            if parts[0] not in result:
                result[parts[0]] = set()
            result[parts[0]].add(parts[1])

    return result
'''





def get_available_keymaps():
    return ALL_KEYMAPS


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
        new_keymap = keymap.replace('(', ' (')
        new_keymap_list.append(new_keymap)
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
