# Kickstart file created by BeanieDeploy.
text

# Enable grapghical.target by default on the installed system
%post 
systemctl set-default graphical.target
%end
