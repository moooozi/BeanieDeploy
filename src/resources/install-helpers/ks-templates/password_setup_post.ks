# Password setup service for first-boot user password configuration
# requires: log_dir, username
# Installs a systemd service that runs before SDDM on first boot to prompt for password

%post --interpreter=/bin/bash --logfile={log_dir}/post_password_setup --nochroot
USERNAME="{username}"

# Create marker file with username
echo "$USERNAME" > /mnt/sysimage/etc/beanie_should_set_password

# Copy password setup script from install media to target system
cp /run/install/repo/install-helpers/beanie-password-setup.py /mnt/sysimage/usr/local/bin/beanie-password-setup
chmod +x /mnt/sysimage/usr/local/bin/beanie-password-setup

# Copy systemd service file from install media to target system
cp /run/install/repo/install-helpers/systemd/beanie-password-setup.service /mnt/sysimage/etc/systemd/system/beanie-password-setup.service

# Enable the service in the target system
chroot /mnt/sysimage systemctl enable beanie-password-setup.service

echo "Password setup service installed and enabled"
%end
