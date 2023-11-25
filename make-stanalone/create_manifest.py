import json
import os

# Get the path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
RELEASEINFO="..\ReleaseInfo.txt"
INPUT="winres\winres.json.template"
OUTPUT="winres\winres.json"
# Read the ReleaseInfo.txt file
with open(RELEASEINFO, 'r') as f:
    lines = f.readlines()

# Extract the AppName and AppVersion
app_info = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in lines if ':' in line}
app_name = app_info.get('AppName', '')
app_version = app_info.get('AppVersion', '')
app_version_base = app_version.split('-')[0]
author = app_info.get('Author', '')


# Read the winres.json file
with open(INPUT, 'r') as f:
    data = json.load(f)

# Update the json data
data['RT_MANIFEST']['#1']['0409']['identity']['name'] = app_name
data['RT_MANIFEST']['#1']['0409']['identity']['version'] = app_version_base
data['RT_VERSION']['#1']['0000']['fixed']['file_version'] = "1.0"
data['RT_VERSION']['#1']['0000']['fixed']['product_version'] = app_version_base
data['RT_VERSION']['#1']['0000']['info']['0409']['ProductName'] = app_name
data['RT_VERSION']['#1']['0000']['info']['0409']['ProductVersion'] = app_version
data['RT_VERSION']['#1']['0000']['info']['0409']['CompanyName'] = ""
data['RT_VERSION']['#1']['0000']['info']['0409']['FileDescription'] = "The quickest way to switch to Fedora Linux"
data['RT_VERSION']['#1']['0000']['info']['0409']['LegalCopyright'] = f"Copyright (c) 2021-2023 {author}"
data['RT_VERSION']['#1']['0000']['info']['0409']['OriginalFilename'] = f"{app_name}-{app_version}-Bundled-Win64.exe"

# Write the updated data back to the winres.json file
with open(OUTPUT, 'w') as f:
    json.dump(data, f, indent=2)
