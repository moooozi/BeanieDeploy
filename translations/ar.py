import APP_INFO

ln_btn_next = "التالي"
ln_btn_back = "السابق"
ln_btn_quit = "إنهاء"
ln_btn_start = "ابدأ"
ln_btn_restart_now = "إعادة التشغيل الآن"
ln_btn_restart_later = "إعادة التشغيل لاحقًا"

ln_check_running = "...جاري التحقق من توافق النظام. الرجاء الانتظار"
ln_check_ram = "التحقق من سعة ذاكرة الوصول العشوائي المتاحة"
ln_check_uefi = "UEFI التحقق من توافق"
ln_check_space = "التحقق من المساحة المتوفرة"
ln_check_resizable = "التحقق من تغيير حجم محرك أقراص النظام"
ln_check_bitlocker = "التحقق من حالة قفل محرك أقراص النظام"

ln_install_running = "...جارٍ التثبيت"

ln_error_title = "على نظامك %s لا يمكن تشغيل" % APP_INFO.SW_NAME
ln_error_list = ":المتطلبات التالية مفقودة"
ln_error_uefi_0 = ".UEFI Boot نظامك لا يدعم (أو لا يستخدم)"
ln_error_uefi_9 = ".UEFI Boot تعذر التحقق من دعم"
ln_error_totalram_0 = ".كافية RAM لا يحتوي نظامك على سعة ذاكرة"
ln_error_totalram_9 = ".فشل التحقق من سعة ذاكرة الوصول العشوائي المتاحة"
ln_error_space_0 = ".لا توجد مساحة كافية على محرك أقراص النظام. حرر بعض المساحة وحاول مرة أخرى"
ln_error_space_9 = ".فشل التحقق من مساحة القرص المتوفرة على محرك أقراص النظام."
ln_error_resizable_0 = ".لا توجد مساحة تقلص كافية على محرك أقراص النظام."
ln_error_resizable_9 = ".فشل التحقق من تغيير حجم محرك أقراص النظام."
ln_error_bitlocker_0 = "لمحرك أقراص النظام. لا يمكن ضمان التوافق على هذا النظام Bitlocker تم تمكين"
ln_error_bitlocker_9 = ".Bitlockerفشل التحقق مما إذا كان محرك أقراص النظام ممكّنًا لـ"

ln_install_question = "؟%s كيف تريد تثبيت" % APP_INFO.distro_name
ln_install_options = ("(موصى به)(%s سطح المكتب) %sتثبيت التلقائي ل" % (APP_INFO.distro_flavors_de[0], APP_INFO.distro_flavors_names[0]),
                       "(%s سطح المكتب) %sتثبيت التلقائي ل" % (APP_INFO.distro_flavors_de[1], APP_INFO.distro_flavors_names[1]),
                       "واختر الحزم لاحقًا net-install متقدم: استخدم ")
ln_install_help = "ساعدني في اتخاذ القرار"

ln_adv_confirm = "تم تحديد الخيار المتقدم ..."
ln_adv_confirm_text = "لقد اخترت خياراً متقدماً وأعرف بالضبط ما أفعله"
ln_windows_question = "وبياناتك؟ Windows حسنًا , ماذا عن "

ln_windows_options = ["Windows بجانب %s تثبيت" % APP_INFO.distro_name,
                      " %s وترحيل مكتبتي (الموسيقى والصور ومقاطع الفيديو) إلى  Windows إزالة" % APP_INFO.distro_name,
                      " %s وجميع البيانات وابدأ من جديد باستخدام Windows إزالة" % APP_INFO.distro_name,
                      "متقدم: لا تفعل شيئًا ودعني أقسم لاحقًا"]
ln_windows_option1_disabled = "(مساحة غير كافية) %s" % ln_windows_options[1]

ln_verify_question = "هذا ما سيتم القيام به. انقر فوق % s عندما تجهز" % ln_btn_start
ln_add_import_wifi = " %s تصدير شبكات واي فاي الخاصة بي إلى" % APP_INFO.distro_name
ln_add_auto_restart = "إعادة التشغيل تلقائيًا"
ln_show_advanced = "إظهار الإعدادات المتقدمة"
ln_adv_torrent = "استخدم تورينت للتنزيل"

ln_old_download_detected = "تم اكتشاف تثبيت غير مكتمل"
ln_old_download_detected_text = "تم اكتشاف تثبيت غير مكتمل ، هل تريد استخدام الملفات التي تم تنزيلها مسبقًا؟" \
                         "(اختر 'لا' للتنظيف وبدء تنزيل جديد)"

ln_job_starting_download = "جار بدء التنزيل"
ln_job_dl_install_media = "جارٍ تنزيل وسائط التثبيت"
ln_dl_timeleft = " الوقت المتبقي "
ln_dl_speed = " السرعة "

ln_job_creating_tmp_part = "إنشاء قرص إقلاع مؤقت لوسائط التثبيت"
ln_job_copying_to_tmp_part = "نسخ ملفات وسائط المثبّت المطلوبة إلى قسم التمهيد المؤقت"
ln_job_adding_tmp_boot_entry = "إضافة إدخالات الإقلاع"

ln_finished_title = "إعادة التشغيل مطلوبة"
ln_finished_text = "إعادة التشغيل مطلوبة لمتابعة التثبيت"

ln_finished_text_restarting_now = "إعادة التشغيل التلقائية خلال %s ثانية"