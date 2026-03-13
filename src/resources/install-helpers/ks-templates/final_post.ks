# Copy all log files to sysimage for post-install review
# requires: log_dir
%post --nochroot --logfile={log_dir}/ks-post-final.log
mkdir -p /mnt/sysimage/var/log/beanie_install_logs 2>/dev/null || true
# Copy logs from the installation process to the installed system for later review
cp {log_dir}/*.log /mnt/sysimage/var/log/beanie_install_logs/ 2>/dev/null || true
%end