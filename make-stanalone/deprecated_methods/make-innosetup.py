import subprocess
import create_manifest

values = {
        "MyAppName": create_manifest.app_name,
        "MyAppVersion": create_manifest.app_version,
        "MyAppVersionBase": create_manifest.app_version_base,
        "MyAppAuthor": create_manifest.author,
        "MyAppCopyright": create_manifest.copyright,
        "MyAppDescription": create_manifest.description,
        "MyAppUrl": create_manifest.app_url,
        "MyDevUrl": create_manifest.dev_url,
    }

compiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
INPUT="innosetup_template.iss"
OUTPUT="innosetup.iss"

with open(INPUT, 'r') as file:
    lines = file.readlines()


# Replace the fields with the predefined values
for i, line in enumerate(lines):
    for key, value in values.items():
        if line.startswith(f"#define {key}"):
            lines[i] = f"#define {key} \"{value}\"\n"


# Write the updated content back to the file
with open(OUTPUT, "w") as file:
    file.writelines(lines)

if __name__ == '__main__':
    subprocess.run([compiler, "innosetup.iss"])