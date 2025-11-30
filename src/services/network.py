"""
Network and download services.
Handles HTTP requests, downloads, WiFi profiles, etc.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import xmltodict  # type: ignore


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
        text=True,
    )
    return result.returncode


def get_wifi_profiles(wifi_profile_dir: str) -> list[dict[str, str]]:
    """
    Extract and parse WiFi profiles from Windows.

    Args:
        wifi_profile_dir: Directory to export profiles to

    Returns:
        List of WiFi profile dictionaries
    """
    profile_path = Path(wifi_profile_dir)

    # Clean and recreate directory
    if profile_path.exists():
        shutil.rmtree(wifi_profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)

    # Export profiles
    extract_wifi_profiles(wifi_profile_dir)
    wifi_profiles: list[dict[str, str]] = []

    for file_path in profile_path.iterdir():
        try:
            with file_path.open() as f:
                xml_content = f.read()
                wifi_profile: dict[str, Any] = xmltodict.parse(xml_content)

                name = wifi_profile["WLANProfile"]["name"]
                ssid = wifi_profile["WLANProfile"]["SSIDConfig"]["SSID"]["name"]

                # Check if network is hidden
                ssid_config = wifi_profile["WLANProfile"]["SSIDConfig"]
                hidden = (
                    "true" if ssid_config.get("nonBroadcast") == "true" else "false"
                )

                # Extract password information
                security = wifi_profile["WLANProfile"]["MSM"]["security"]["sharedKey"]
                password = security["keyMaterial"]

                profile: dict[str, str] = {
                    "name": name,
                    "ssid": ssid,
                    "hidden": hidden,
                    "password": password,
                }
                wifi_profiles.append(profile)

        except KeyError:
            logging.warning(
                f"Skipping file {file_path.name} due to missing expected keys"
            )
            continue

    # Clean up
    shutil.rmtree(wifi_profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)

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

    parsed_url = urlparse(url)
    return Path(parsed_url.path).name
