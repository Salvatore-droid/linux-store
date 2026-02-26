# store/utils.py - Complete updated file

import subprocess
import time
from django.conf import settings

class PyStore:
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
    def flatpak_search(app):
        try:
            # Get search results
            result = subprocess.run(
                ["flatpak", "search", app, "--columns=application,name,description,version"], 
                capture_output=True, 
                text=True,
                check=True
            )
            
            # Parse the output into structured data
            apps = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header line
            start_idx = 1 if lines and lines[0].startswith('Application ID') else 0
            
            for line in lines[start_idx:]:
                if line.strip():
                    # Split by tab
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        app_id = parts[0].strip()
                        name = parts[1].strip() if len(parts) > 1 else app_id.split('.')[-1]
                        description = parts[2].strip() if len(parts) > 2 else ''
                        version = parts[3].strip() if len(parts) > 3 else 'Unknown'
                        
                        # Get icon URL (simplified, no API calls)
                        icon_url = PyStore.get_app_icon_url(app_id, name)
                        
                        # Check if app is already installed
                        is_installed = PyStore.is_app_installed(app_id)
                        
                        apps.append({
                            'app_id': app_id,
                            'name': name,
                            'description': description,
                            'version': version,
                            'icon_url': icon_url,
                            'is_installed': is_installed
                        })
            
            return apps
        except subprocess.CalledProcessError as e:
            print(f"Search error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    @staticmethod
    def get_app_icon_url(app_id, app_name):
        """Get icon URL for an app - simplified version that won't break search"""
        try:
            # Extract the last part of app_id for the icon name
            icon_name = app_id.split('.')[-1].lower()
            
            # Try multiple possible Flathub icon URLs (these are more reliable)
            possible_urls = [
                f"https://dl.flathub.org/repo/appstream/x86_64/icons/128x128/{app_id}.png",
                f"https://dl.flathub.org/media/{app_id}/icon-128x128.png",
                f"https://flathub.org/repo/appstream/x86_64/icons/128x128/{app_id}.png",
            ]
            
            # We'll return the first URL pattern - the browser will handle 404s
            # and the onerror in the template will show the fallback
            return possible_urls[0]
            
        except Exception as e:
            # If anything fails, return a UI Avatar fallback
            return f"https://ui-avatars.com/api/?name={app_name}&size=128&background=6366f1&color=fff&length=2&rounded=true"

    @staticmethod
    def is_app_installed(app_id):
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
    def run_app(app_id):
        try:
            subprocess.run(["flatpak", "run", app_id], check=True)
            return True
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def check_flatpak():
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
    def run_command(command):
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
    def install_app(app_id):
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
    def get_installed_app_info(app_id):
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
    def uninstall_app(app_id):
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
    def install_app_with_progress(app_id, progress_callback=None):
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
    def install_app_with_realtime_output(app_id, callback=None):
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