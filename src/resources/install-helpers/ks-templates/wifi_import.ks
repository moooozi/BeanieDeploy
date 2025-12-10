# Importing Wi-Fi profiles
# requires: wifi_profiles_dir_name, log_dir

%post --nochroot --logfile={log_dir}/ks-post_wifi.log
mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections
cp /run/install/repo/{wifi_profiles_dir_name}/*.* /mnt/sysimage/etc/NetworkManager/system-connections
# Set proper permissions for security
chmod 600 /mnt/sysimage/etc/NetworkManager/system-connections/*
# Validate by listing copied profiles
echo "Copied WiFi profiles:" >> {log_dir}/ks-post_wifi.log
ls -la /mnt/sysimage/etc/NetworkManager/system-connections/ >> {log_dir}/ks-post_wifi.log
%end