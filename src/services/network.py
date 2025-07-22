"""
Network and download services.
Handles HTTP requests, downloads, WiFi profiles, etc.
"""
import json
import os
import subprocess
import time
import urllib.request
import webbrowser
from typing import Optional, List, Dict, Any
from urllib.request import urlopen

import xmltodict


def open_url(url: str) -> None:
    """
    Open a URL in the default web browser.
    
    Args:
        url: URL to open
    """
    webbrowser.open_new_tab(url)


def get_json(url: str, queue=None, named: Optional[str] = None) -> Any:
    """
    Fetch and parse JSON from a URL.
    
    Args:
        url: URL to fetch JSON from
        queue: Optional queue for async operations
        named: Optional name to return as tuple
        
    Returns:
        Parsed JSON data, or tuple with name if named is provided
    """
    response = urlopen(url).read()
    data = json.loads(response)
    
    return_value = (named, data) if named else data
    
    if queue:
        queue.put(return_value)
    else:
        return return_value


def download_with_standard_lib(
    url: str, 
    destination: str, 
    output_name: Optional[str] = None, 
    queue=None
) -> int:
    """
    Download a file using Python's standard library.
    
    DEPRECATED: Use services.download.DownloadService instead for new code.
    
    Args:
        url: URL to download from
        destination: Destination directory
        output_name: Optional custom filename
        queue: Optional queue for progress updates
        
    Returns:
        1 if successful
    """
    import warnings
    warnings.warn(
        "download_with_standard_lib is deprecated. Use services.download.DownloadService instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    local_filename = output_name if output_name else url.split("/")[-1]
    local_filepath = os.path.join(destination, local_filename)

    tracker = {
        "type": "dl_tracker",
        "file_name": local_filename,
        "status": "downloading",
        "speed": "0",
        "eta": "N/A",
        "size": "0",
        "%": "0",
    }

    with urllib.request.urlopen(url) as response:
        total_size = int(response.getheader("Content-Length").strip())
        tracker["size"] = str(total_size)
        downloaded_size = 0
        start_time = time.time()
        last_update_time = start_time

        with open(local_filepath, "wb") as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded_size += len(chunk)
                elapsed_time = time.time() - start_time
                
                if elapsed_time > 0:
                    speed = downloaded_size / elapsed_time
                    eta = (total_size - downloaded_size) / speed if speed > 0 else "N/A"
                else:
                    speed = 0
                    eta = "N/A"
                
                tracker["speed"] = f"{speed:.2f}"
                tracker["eta"] = f"{eta:.2f}" if eta != "N/A" else "N/A"
                tracker["%"] = str(int((downloaded_size / total_size) * 100))

                current_time = time.time()
                if current_time - last_update_time >= 0.5:
                    if queue:
                        queue.put(tracker)
                    last_update_time = current_time

    tracker["status"] = "complete"
    if queue:
        queue.put(tracker)
    return 1


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


def parse_xml(xml: str) -> Dict[str, Any]:
    """
    Parse XML string into a dictionary.
    
    Args:
        xml: XML string to parse
        
    Returns:
        Parsed XML as dictionary
    """
    return xmltodict.parse(xml)


def get_wifi_profiles(wifi_profile_dir: str) -> List[Dict[str, str]]:
    """
    Extract and parse WiFi profiles from Windows.
    
    Args:
        wifi_profile_dir: Directory to export profiles to
        
    Returns:
        List of WiFi profile dictionaries
    """
    from services.file import rmdir, mkdir
    from pathlib import Path
    
    # Clean and recreate directory
    rmdir(wifi_profile_dir)
    mkdir(Path(wifi_profile_dir))

    # Export profiles
    extract_wifi_profiles(wifi_profile_dir)
    wifi_profiles = []
    
    for filename in os.listdir(wifi_profile_dir):
        try:
            with open(os.path.join(wifi_profile_dir, filename), "r") as f:
                xml_content = f.read()
                wifi_profile: dict = parse_xml(xml_content)
                
                name = wifi_profile["WLANProfile"]["name"]
                ssid = wifi_profile["WLANProfile"]["SSIDConfig"]["SSID"]["name"]
                
                # Check if network is hidden
                ssid_config = wifi_profile["WLANProfile"]["SSIDConfig"]
                hidden = "true" if ssid_config.get("nonBroadcast") == "true" else "false"
                
                # Extract password information
                security = wifi_profile["WLANProfile"]["MSM"]["security"]["sharedKey"]
                password = security["keyMaterial"]
                
                profile = {
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
    rmdir(wifi_profile_dir)
    mkdir(Path(wifi_profile_dir))
    
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
