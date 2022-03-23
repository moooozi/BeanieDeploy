import APP_INFO

ln_btn_next = "التالي"
ln_btn_back = "السابق"
ln_btn_quit = "إنهاء"
ln_btn_start = "ابدأ"

ln_check_running = "...جاري التحقق من توافق النظام. الرجاء الانتظار"
ln_install_running = "...جارٍ التثبيت"

ln_error_title = "على نظامك %s لا يمكن تشغيل" % APP_INFO.SW_NAME
ln_error_uefi_0 = ".UEFI Boot نظامك لا يدعم (أو لا يستخدم)"
ln_error_uefi_9 = ".UEFI Boot تعذر التحقق من دعم "
ln_error_totalram_0 = ".كافية RAM لا يحتوي نظامك على سعة ذاكرة"
ln_error_totalram_9 = ".فشل التحقق من سعة ذاكرة الوصول العشوائي المتاحة"
ln_error_space_0 = ".لا توجد مساحة كافية على محرك أقراص النظام. حرر بعض المساحة وحاول مرة أخرى"
ln_error_space_9 = ".فشل التحقق من مساحة القرص المتوفرة على محرك أقراص النظام."
ln_error_resizable_0 = ".فشل التحقق من تغيير حجم محرك أقراص النظام."
ln_error_resizable_9 = ".لا توجد مساحة تقلص كافية على محرك أقراص النظام."
ln_error_bitlocker_0 = ".Bitlockerفشل التحقق مما إذا كان محرك أقراص النظام ممكّنًا لـ"
ln_error_bitlocker_9 = "لمحرك أقراص النظام. لا يمكن ضمان التوافق على هذا النظام Bitlocker تم تمكين"

ln_install_question = "؟%s كيف تريد تثبيت" % APP_INFO.distro_name

ln_install_options = [0, "KDE تثبيت سريع مع سطح مكتب",
                      "GNOME التثبيت السريع مع سطح مكتب",
                      "متقدم: دعني أقوم بتهيئة تطبيقاتي لاحقًا"]

ln_windows_question = "وبياناتك؟ Windows حسنًا , ماذا عن "

ln_windows_options = [0, "Windows بجانب %s تثبيت" % APP_INFO.distro_name,
                      " %s وترحيل مكتبتي (الموسيقى والصور ومقاطع الفيديو) إلى  Windows إزالة" % APP_INFO.distro_name,
                      " %s وجميع البيانات وابدأ من جديد باستخدام Windows إزالة" % APP_INFO.distro_name,
                      "متقدم: لا تفعل شيئًا ودعني أقسم لاحقًا"]
ln_windows_option1_disabled = "(مساحة غير كافية) %s" % ln_windows_options[1]

ln_verify_question = "هذا ما سيتم القيام به. انقر فوق % s عندما تجهز" % ln_btn_start

ln_job_downloading_install_media = "تنزيل وسائط التثبيت"
