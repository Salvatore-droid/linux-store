# store/utils.py - Complete updated file with Flathub API integration

import subprocess
import time
import requests
from django.conf import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FlathubAPI:
    """Interface for Flathub API v2"""
    BASE_URL = "https://flathub.org/api/v2"
    
    @staticmethod
    def search(query: str, locale: str = "en") -> List[Dict]:
        """
        Search for applications using Flathub API.
        
        Args:
            query: Search query string
            locale: Language locale (default: 'en')
            
        Returns:
            List of application dictionaries with metadata
        """
        try:
            url = f"{FlathubAPI.BASE_URL}/search"
            payload = {
                "query": query,
                "limit": 50
            }
            
            response = requests.post(url, json=payload, params={"locale": locale}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            apps = []
            
            if "hits" in data:
                for result in data["hits"]:
                    app_data = {
                        'app_id': result.get('app_id', ''),
                        'name': result.get('name', ''),
                        'description': result.get('description', ''),
                        'version': result.get('current_release', {}).get('version', 'Unknown'),
                        'icon_url': FlathubAPI.get_app_icon_url(result.get('app_id', '')),
                        'is_installed': False,  # Will be checked later
                        'summary': result.get('summary', ''),
                        'category': result.get('categories', ['Other'])[0] if result.get('categories') else 'Other',
                        'rating': result.get('rating', 0),
                        'download_count': result.get('download_count', 0),
                    }
                    apps.append(app_data)
            
            return apps
        except requests.exceptions.RequestException as e:
            logger.error(f"Flathub API search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return []
    
    @staticmethod
    def get_app_details(app_id: str, locale: str = "en") -> Optional[Dict]:
        """
        Get detailed information about a specific application.
        
        Args:
            app_id: Application ID
            locale: Language locale (default: 'en')
            
        Returns:
            Dictionary with app details or None if not found
        """
        try:
            url = f"{FlathubAPI.BASE_URL}/appstream/{app_id}"
            response = requests.get(url, params={"locale": locale}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                return {
                    'app_id': data.get('id', app_id),
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'summary': data.get('summary', ''),
                    'version': data.get('current_release', {}).get('version', 'Unknown'),
                    'icon_url': FlathubAPI.get_app_icon_url(app_id),
                    'screenshots': data.get('screenshots', []),
                    'url': data.get('url', ''),
                    'license': data.get('metadata_license', 'Unknown'),
                    'developer_name': data.get('developer_name', 'Unknown'),
                    'categories': data.get('categories', []),
                    'rating': data.get('rating', 0),
                    'download_count': data.get('download_count', 0),
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Flathub API details error for {app_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting app details: {e}")
            return None
    
    @staticmethod
    def get_popular_apps(limit: int = 20, locale: str = "en") -> List[Dict]:
        """
        Get popular applications from Flathub.
        
        Args:
            limit: Number of apps to return
            locale: Language locale (default: 'en')
            
        Returns:
            List of popular application dictionaries
        """
        try:
            # Use search endpoint with empty query to get popular apps
            url = f"{FlathubAPI.BASE_URL}/search"
            payload = {
                "query": "",
                "limit": limit
            }
            
            response = requests.post(url, json=payload, params={"locale": locale}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            apps = []
            
            if "hits" in data:
                for result in data["hits"][:limit]:
                    app_data = {
                        'app_id': result.get('app_id', ''),
                        'name': result.get('name', ''),
                        'description': result.get('description', ''),
                        'version': result.get('current_release', {}).get('version', 'Unknown') if isinstance(result.get('current_release'), dict) else 'Unknown',
                        'icon_url': FlathubAPI.get_app_icon_url(result.get('app_id', '')),
                        'is_installed': False,
                        'download_count': result.get('download_count', 0),
                    }
                    apps.append(app_data)
            
            return apps
        except requests.exceptions.RequestException as e:
            logger.error(f"Flathub API popular apps error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting popular apps: {e}")
            return []
    
    @staticmethod
    def get_app_icon_url(app_id: str) -> str:
        """
        Get the icon URL for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            URL to the app icon or fallback avatar URL
        """
        try:
            if not app_id:
                return f"https://ui-avatars.com/api/?name=App&size=128&background=6366f1&color=fff"
            
            # Try multiple possible Flathub icon URLs
            possible_urls = [
                f"https://dl.flathub.org/repo/appstream/x86_64/icons/128x128/{app_id}.png",
                f"https://dl.flathub.org/media/{app_id}/icon-128x128.png",
                f"https://flathub.org/repo/appstream/x86_64/icons/128x128/{app_id}.png",
            ]
            
            # Return the first URL - browser will handle 404s
            return possible_urls[0]
        except Exception:
            app_name = app_id.split('.')[-1] if app_id else 'App'
            return f"https://ui-avatars.com/api/?name={app_name}&size=128&background=6366f1&color=fff"


class PyStore:
    """Main store interface combining Flathub API and local system management"""
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        """
        Search for applications using Flathub API.
        
        Args:
            query: Search query string
            
        Returns:
            List of application dictionaries
        """
        if not query or query.lower() == 'quit':
            return []
        
        apps = FlathubAPI.search(query)
        
        # Check which apps are installed
        for app in apps:
            app['is_installed'] = PyStore.is_app_installed(app['app_id'])
        
        return apps
    
    @staticmethod
    def flatpak_search(app: str) -> List[Dict]:
        """
        Legacy search method for backward compatibility.
        Uses Flathub API instead of flatpak command.
        
        Args:
            app: Search query string
            
        Returns:
            List of application dictionaries
        """
        return PyStore.search(app)
    
    @staticmethod
    def get_app_details(app_id: str) -> Optional[Dict]:
        """
        Get detailed information about an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary with app details or None
        """
        details = FlathubAPI.get_app_details(app_id)
        
        if details:
            details['is_installed'] = PyStore.is_app_installed(app_id)
        
        return details
    
    @staticmethod
    def get_popular_apps(limit: int = 20) -> List[Dict]:
        """
        Get popular applications.
        
        Args:
            limit: Number of apps to return
            
        Returns:
            List of popular application dictionaries
        """
        apps = FlathubAPI.get_popular_apps(limit)
        
        # Check which apps are installed
        for app in apps:
            app['is_installed'] = PyStore.is_app_installed(app['app_id'])
        
        return apps
    
    @staticmethod
    def install_pyfiglet():
        try:
            subprocess.run(["sudo", "apt", "install", "python3-pyfiglet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def get_app_icon_url(app_id: str, app_name: str = None) -> str:
        """Get icon URL for an app"""
        return FlathubAPI.get_app_icon_url(app_id)

    @staticmethod
    def is_app_installed(app_id: str) -> bool:
        """Check if an app is already installed"""
        try:
            result = subprocess.run(
                ["flatpak", "info", app_id],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def run_app(app_id: str):
        try:
            subprocess.run(["flatpak", "run", app_id], check=True)
            return True
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def check_flatpak() -> bool:
        try:
            subprocess.run(["which", "flatpak"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         text=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def run_command(command: List[str]) -> bool:
        try:
            subprocess.run(command, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         text=True, 
                         check=True)
            return True
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def install_flatpak():
        results = []
        results.append(("Updating system...", PyStore.run_command(["sudo", "apt", "update"])))
        results.append(("Installing flatpak...", PyStore.run_command(["sudo", "apt", "install", "-y", "flatpak"])))
        results.append(("Adding flathub repository...", 
                      PyStore.run_command(["flatpak", "remote-add", "--if-not-exists", "flathub", "https://flathub.org/repo/flathub.flatpakrepo"])))
        return results

    @staticmethod
    def install_app(app_id: str):
        try:
            result = subprocess.run(["flatpak", "install", "-y", "--verbose", "flathub", app_id], 
                                capture_output=True, 
                                text=True,
                                check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}"

    @staticmethod
    def check_pyfiglet():
        try:
            subprocess.run(["pip", "list", "|", "grep", "pyfiglet"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         text=True,
                         check=True)
            return True
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def check_flatpak_working():
        """Verify Flatpak can install apps"""
        try:
            test_app = "org.gnome.Calculator"  # A small, reliable test app
            result = subprocess.run(["flatpak", "install", "-y", "flathub", test_app],
                                capture_output=True,
                                text=True)
            if result.returncode == 0:
                return True, "Flatpak working correctly"
            return False, f"Test failed: {result.stderr}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_installed_apps():
        try:
            result = subprocess.run(
                ["flatpak", "list", "--columns=application,version,size"],
                capture_output=True,
                text=True,
                check=True
            )
            
            apps = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        apps.append({
                            'app_id': parts[0],
                            'version': parts[1],
                            'size': parts[2],
                        })
            return apps
        except subprocess.CalledProcessError as e:
            return []

    @staticmethod
    def get_installed_app_info(app_id: str) -> Optional[Dict]:
        """Get actual installed app information"""
        try:
            result = subprocess.run(
                ['flatpak', 'info', app_id],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return None
                
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    info[key.strip().lower()] = val.strip()
            
            return info
        except:
            return None

    @staticmethod
    def uninstall_app(app_id: str):
        try:
            result = subprocess.run(
                ["flatpak", "uninstall", "-y", app_id],
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    @staticmethod
    def install_app_with_progress(app_id: str, progress_callback=None):
        try:
            process = subprocess.Popen(
                ["flatpak", "install", "-y", "--verbose", "flathub", app_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if progress_callback:
                        progress_callback(output.strip())
            
            if process.returncode == 0:
                return True, "Installation completed successfully"
            else:
                return False, f"Installation failed with return code {process.returncode}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def install_app_with_realtime_output(app_id: str, callback=None):
        """Install app with real-time output capturing"""
        try:
            process = subprocess.Popen(
                ["flatpak", "install", "-y", "--verbose", "flathub", app_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            return_code = None
            
            while True:
                line = process.stdout.readline()
                if line == '' and process.poll() is not None:
                    return_code = process.poll()
                    break
                if line:
                    line = line.strip()
                    output_lines.append(line)
                    if callback:
                        callback(line)
            
            # Check for success indicators in output
            if return_code == 0:
                # Also check if there are any error messages in the output
                error_indicators = ['error:', 'failed:', 'cannot install', 'unable to']
                last_lines = ' '.join(output_lines[-10:]).lower()
                
                if any(indicator in last_lines for indicator in error_indicators):
                    return False, "Installation completed with warnings: " + ' '.join(output_lines[-3:])
                
                return True, "Installation completed successfully"
            else:
                error_msg = f"Flatpak returned error code {return_code}"
                if output_lines:
                    error_msg += ": " + output_lines[-1]
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Installation timed out"
        except Exception as e:
            return False, str(e)
