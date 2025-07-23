"""
Business logic for PageVerify: review text construction.
"""
def build_review_text(selected_spin, kickstart, install_options, LN):
    review_sel = []
    if kickstart and getattr(kickstart, 'partition_method', None) == "custom":
        review_sel.append(LN.verify_text["no_autoinst"] % selected_spin.name)
    else:
        if kickstart and getattr(kickstart, 'partition_method', None) == "dualboot":
            review_sel.append(LN.verify_text["autoinst_dualboot"] % selected_spin.name)
            review_sel.append(LN.verify_text["autoinst_keep_data"])
        elif kickstart and getattr(kickstart, 'partition_method', None) == "replace_win":
            review_sel.append(LN.verify_text["autoinst_replace_win"] % selected_spin.name)
            review_sel.append(LN.verify_text["autoinst_rm_all"])
        if install_options and getattr(install_options, 'export_wifi', False):
            review_sel.append(LN.verify_text["autoinst_wifi"] % selected_spin.name)
    return review_sel
