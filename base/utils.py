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
                      PyStore.run_command(["flatpak", "remote-add", "--if-not-exists", "flathub", 
                                         "https://flathub.org/repo/flathub.flatpakrepo"])))
        return results

    @staticmethod
    def install_app(app_id):
        try:
            result = subprocess.run(["flatpak", "install", "flathub", app_id], 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, str(e)

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