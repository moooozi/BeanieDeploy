import os
import subprocess
import time
import create_manifest
metadata = create_manifest.create_manifest()

script_dir = os.path.dirname(os.path.abspath(__file__))


values = {
        "MyAppName": create_manifest.app_name,
        "MyAppVersion": create_manifest.app_version,
        "MyAppVersionBase": create_manifest.app_version_base,
        "MyAppAuthor": create_manifest.author,
        "MyAppCopyright": create_manifest.copyright,
        "MyAppDescription": create_manifest.description,
        "MyAppUrl": create_manifest.app_url,
        "MyDevUrl": create_manifest.dev_url,
        "SourcePath": '../release',
        "OutputFileName": "../output/" + metadata['OriginalFilename'],
        "IconPath": fr"{script_dir}\winres\icon.ico",

    }

compiler = r"C:\Program Files (x86)\NSIS\makensis.exe"
INPUT="nsis_template.nsi"
OUTPUT=".cache_nsis.nsi"

with open(INPUT, 'r') as file:
    lines = file.readlines()


# Replace the fields with the predefined values
for i, line in enumerate(lines):
    lines[i] = line.format(**values)
    if line.startswith(f"; Metadata"):
        for j, (metadata_key, metadata_value) in enumerate(metadata.items()):
            lines.insert(i+j+1, f'VIAddVersionKey "{metadata_key}" "{metadata_value}"\n')
        lines.insert(i+1, f"VIProductVersion 1.0.0.0\n")
                
# Write the updated content back to the file
with open(OUTPUT, "w") as file:
    file.writelines(lines)

if __name__ == '__main__':
    subprocess.run([compiler, OUTPUT], shell=True)
    time.sleep(5)