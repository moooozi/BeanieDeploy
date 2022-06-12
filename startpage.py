import wmi

c = wmi.WMI()

video =  c.Win32_videocontroller
print video.properties