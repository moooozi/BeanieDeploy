"""
Network and download services.
Handles HTTP requests, downloads, WiFi profiles, etc.
"""
import os
import shutil
import subprocess
from typing import List, Dict, Any

import xmltodict



def extract_wifi_profiles(folder_path: str) -> int:
    """
    Export Windows WiFi profiles to a folder.
    
    Args:
        folder_path: Folder to export profiles to
        
    Returns:
        Command return code (0 = success)
    """
    args = ["netsh", "wlan", "export", "profile", "key=clear", f"folder={folder_path}"]
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return result.returncode

def get_wifi_profiles(wifi_profile_dir: str) -> List[Dict[str, str]]:
    """
    Extract and parse WiFi profiles from Windows.
    
    Args:
        wifi_profile_dir: Directory to export profiles to
        
    Returns:
        List of WiFi profile dictionaries
    """
    from pathlib import Path
    
    # Clean and recreate directory
    if Path(wifi_profile_dir).exists():
        shutil.rmtree(wifi_profile_dir)
    Path(wifi_profile_dir).mkdir(parents=True, exist_ok=True)

    # Export profiles
    extract_wifi_profiles(wifi_profile_dir)
    wifi_profiles: List[Dict[str, str]] = []
    
    for filename in os.listdir(wifi_profile_dir):
        try:
            with open(os.path.join(wifi_profile_dir, filename), "r") as f:
                xml_content = f.read()
                wifi_profile: Dict[str, Any] = xmltodict.parse(xml_content)
                
                name = wifi_profile["WLANProfile"]["name"]
                ssid = wifi_profile["WLANProfile"]["SSIDConfig"]["SSID"]["name"]
                
                # Check if network is hidden
                ssid_config = wifi_profile["WLANProfile"]["SSIDConfig"]
                hidden = "true" if ssid_config.get("nonBroadcast") == "true" else "false"
                
                # Extract password information
                security = wifi_profile["WLANProfile"]["MSM"]["security"]["sharedKey"]
                password = security["keyMaterial"]
                
                profile: Dict[str, str] = {
                    "name": name,
                    "ssid": ssid,
                    "hidden": hidden,
                    "password": password,
                }
                wifi_profiles.append(profile)
                
        except KeyError:
            print("Note: a WiFi profile could not be exported, so it will be skipped")
            continue

    # Clean up
    shutil.rmtree(wifi_profile_dir)
    Path(wifi_profile_dir).mkdir(parents=True, exist_ok=True)
    
    return wifi_profiles


def get_file_name_from_url(url: str) -> str:
    """
    Extract filename from a URL.
    
    Args:
        url: URL to extract filename from
        
    Returns:
        Filename from the URL
    """
    from urllib.parse import urlparse
    import os
    
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)
