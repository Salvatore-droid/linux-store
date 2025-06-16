# store/utils.py
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
            result = subprocess.run(["flatpak", "search", app], 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error, search not found {app}: {e}"

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
            import subprocess
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

    # utils.py
    # Add this method to your PyStore class
    @staticmethod
    def install_app_with_progress(app_id, progress_callback=None):
        try:
            process = subprocess.Popen(
                ["flatpak", "install", "-y", "--verbose", "flathub", app_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
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