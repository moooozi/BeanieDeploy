# Copy all log files to sysimage for post-install review
# requires: log_dir
%post --nochroot --logfile={log_dir}/ks-post-final.log
mkdir -p /mnt/sysimage{log_dir}
cp {log_dir}/*.log /mnt/sysimage{log_dir}/
%end