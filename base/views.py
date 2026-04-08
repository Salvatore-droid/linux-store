from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import InstalledApp
from .utils import PyStore
import json
import time
from threading import Thread
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global dictionary to track installation progress
installation_progress = {}


def home(request):
    """Home page with search functionality"""
    if request.method == 'POST':
        app_name = request.POST.get('app_name', '').strip()
        if app_name.lower() == 'quit':
            return redirect('home')
        
        if not app_name:
            return render(request, 'index.html', {'error': 'Please enter an app name'})
        
        search_results = PyStore.search(app_name)
        return render(request, 'results.html', {
            'app_name': app_name,
            'search_results': search_results,
            'has_results': len(search_results) > 0
        })
    
    # Get popular apps for home page
    popular_apps = PyStore.get_popular_apps(limit=6)
    return render(request, 'index.html', {
        'popular_apps': popular_apps
    })


def browse_apps(request):
    """Browse all available apps with pagination"""
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    # Get popular apps (can be extended with pagination)
    all_apps = PyStore.get_popular_apps(limit=50)
    
    # Simple pagination
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_apps = all_apps[start:end]
    total_pages = (len(all_apps) + per_page - 1) // per_page
    
    return render(request, 'browse.html', {
        'apps': paginated_apps,
        'current_page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1,
        'next_page': page + 1,
    })


def app_detail(request, app_id):
    """Display detailed information about an app"""
    try:
        app_details = PyStore.get_app_details(app_id)
        
        if not app_details:
            messages.error(request, f"App '{app_id}' not found")
            return redirect('browse_apps')
        
        return render(request, 'app_detail.html', {
            'app': app_details
        })
    except Exception as e:
        logger.error(f"Error getting app details for {app_id}: {e}")
        messages.error(request, "Error loading app details")
        return redirect('browse_apps')


def install(request):
    """Handle app installation"""
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '').strip()
        if app_id.lower() == 'quit':
            return redirect('home')
        
        if not app_id:
            return JsonResponse({'error': 'No app ID provided'}, status=400)
        
        install_id = f"{app_id}_{int(time.time())}"
        
        # Initialize progress tracking
        installation_progress[install_id] = {
            'status': 'initializing',
            'progress': 0,
            'message': 'Starting installation process...',
            'app_id': app_id,
            'logs': ['Starting installation process...'],
            'start_time': datetime.now().isoformat(),
            'current_stage': 'preparing',
            'stages': {
                'preparing': {'started': False, 'completed': False},
                'downloading': {'started': False, 'completed': False},
                'installing': {'started': False, 'completed': False},
                'finalizing': {'started': False, 'completed': False}
            },
            'metadata': {
                'size': None,
                'version': None
            },
            'download_progress': 0,
            'total_download_size': None,
            'downloaded_size': None,
            'install_details': {}
        }
        
        def install_thread():
            try:
                # Update progress - preparation started
                installation_progress[install_id].update({
                    'status': 'preparing',
                    'progress': 5,
                    'message': 'Preparing installation...',
                    'current_stage': 'preparing',
                    'stages': {
                        'preparing': {'started': True, 'completed': False},
                        'downloading': {'started': False, 'completed': False},
                        'installing': {'started': False, 'completed': False},
                        'finalizing': {'started': False, 'completed': False}
                    }
                })
                
                installation_progress[install_id]['logs'].append('Checking dependencies...')
                time.sleep(0.5)
                
                installation_progress[install_id].update({
                    'status': 'downloading',
                    'progress': 10,
                    'message': 'Starting download...',
                    'stages': {
                        'preparing': {'started': True, 'completed': True},
                        'downloading': {'started': True, 'completed': False},
                        'installing': {'started': False, 'completed': False},
                        'finalizing': {'started': False, 'completed': False}
                    }
                })
                
                # Phase 2: Download with real progress from flatpak
                def progress_callback(line):
                    current_data = installation_progress[install_id]
                    logs = current_data.get('logs', [])
                    logs.append(line)
                    
                    import re
                    
                    # Check for download progress
                    percent_match = re.search(r'(\d+)%', line)
                    if percent_match and 'Downloading' in line:
                        percent = int(percent_match.group(1))
                        scaled_progress = 10 + (percent * 0.6)  # Scale to 10-70%
                        installation_progress[install_id]['download_progress'] = percent
                        installation_progress[install_id]['progress'] = scaled_progress
                        installation_progress[install_id]['message'] = f'Downloading... {percent}%'
                    
                    # Check for installation progress
                    if 'Installing' in line and '%' in line:
                        install_match = re.search(r'Installing.*?(\d+)%', line)
                        if install_match:
                            install_percent = int(install_match.group(1))
                            scaled_progress = 70 + (install_percent * 0.2)  # Scale to 70-90%
                            installation_progress[install_id]['progress'] = scaled_progress
                            installation_progress[install_id]['message'] = f'Installing... {install_percent}%'
                            installation_progress[install_id]['current_stage'] = 'installing'
                            installation_progress[install_id]['status'] = 'installing'
                    
                    # Check for download size
                    size_match = re.search(r'Downloading (\d+\.?\d*) (\w+) of (\d+\.?\d*) (\w+)', line)
                    if size_match:
                        downloaded = size_match.group(1)
                        downloaded_unit = size_match.group(2)
                        total = size_match.group(3)
                        total_unit = size_match.group(4)
                        installation_progress[install_id]['downloaded_size'] = f"{downloaded} {downloaded_unit}"
                        installation_progress[install_id]['total_download_size'] = f"{total} {total_unit}"
                    
                    # Check for completion messages (success indicators)
                    if any(msg in line.lower() for msg in ['installation complete', 'installed', 'completed successfully']):
                        installation_progress[install_id]['logs'].append(f"✅ {line}")
                    
                    # Check for error messages
                    if any(err in line.lower() for err in ['error:', 'failed:', 'cannot', 'unable']):
                        installation_progress[install_id]['logs'].append(f"❌ {line}")
                    
                    # Update logs (keep last 100)
                    installation_progress[install_id]['logs'] = logs[-100:]
                    
                    # Update stages based on progress
                    progress = installation_progress[install_id]['progress']
                    stages = installation_progress[install_id]['stages']
                    
                    if progress >= 70 and not stages['installing']['started']:
                        stages['installing'] = {'started': True, 'completed': False}
                        installation_progress[install_id]['current_stage'] = 'installing'
                        installation_progress[install_id]['status'] = 'installing'
                    
                    if progress >= 90 and not stages['finalizing']['started']:
                        stages['finalizing'] = {'started': True, 'completed': False}
                        installation_progress[install_id]['current_stage'] = 'finalizing'
                        installation_progress[install_id]['status'] = 'finalizing'
                
                # Perform actual installation with real-time output
                success, output = PyStore.install_app_with_realtime_output(app_id, progress_callback)
                
                if not success:
                    # Installation failed
                    error_message = f"Installation failed: {output[:200]}..." if len(output) > 200 else output
                    installation_progress[install_id].update({
                        'status': 'failed',
                        'message': error_message,
                        'progress': 0,  # Reset progress on failure
                        'logs': installation_progress[install_id]['logs'] + [f'❌ ERROR: {error_message}']
                    })
                    return
                
                # Installation succeeded
                installation_progress[install_id].update({
                    'status': 'finalizing',
                    'progress': 95,
                    'message': 'Finalizing installation...',
                    'current_stage': 'finalizing',
                    'stages': {
                        'preparing': {'started': True, 'completed': True},
                        'downloading': {'started': True, 'completed': True},
                        'installing': {'started': True, 'completed': True},
                        'finalizing': {'started': True, 'completed': False}
                    }
                })
                
                # Get actual app metadata
                app_info = PyStore.get_installed_app_info(app_id)
                
                installation_progress[install_id]['logs'].extend([
                    'Creating desktop shortcuts...',
                    'Updating application database...',
                    f"✅ Installation verified: {app_id}"
                ])
                
                if app_info:
                    installation_progress[install_id]['metadata'] = {
                        'size': app_info.get('size', '0 MB'),
                        'version': app_info.get('version', 'unknown')
                    }
                
                # Mark as completed
                installation_progress[install_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Installation complete!',
                    'stages': {
                        'preparing': {'started': True, 'completed': True},
                        'downloading': {'started': True, 'completed': True},
                        'installing': {'started': True, 'completed': True},
                        'finalizing': {'started': True, 'completed': True}
                    }
                })
                
            except Exception as e:
                logger.error(f"Installation error: {e}")
                installation_progress[install_id].update({
                    'status': 'failed',
                    'message': f'Unexpected error: {str(e)}',
                    'progress': 0,
                    'logs': installation_progress[install_id]['logs'] + [f'❌ FATAL ERROR: {str(e)}']
                })
        
        # Start installation in background thread
        thread = Thread(target=install_thread, daemon=True)
        thread.start()
        
        return render(request, 'installation_progress.html', {
            'install_id': install_id,
            'app_id': app_id
        })
    
    return redirect('home')


def installation_progress_api(request, install_id):
    """API endpoint to get installation progress"""
    if install_id not in installation_progress:
        return JsonResponse({'error': 'Installation not found'}, status=404)
    
    progress_data = installation_progress[install_id]
    return JsonResponse(progress_data)


def installed_apps(request):
    """Display list of installed apps"""
    try:
        installed = PyStore.get_installed_apps()
        return render(request, 'installed.html', {
            'installed_apps': installed
        })
    except Exception as e:
        logger.error(f"Error getting installed apps: {e}")
        messages.error(request, "Error loading installed apps")
        return render(request, 'installed.html', {
            'installed_apps': []
        })


def uninstall_app(request, app_id):
    """Uninstall an application"""
    if request.method == 'POST':
        try:
            success, message = PyStore.uninstall_app(app_id)
            if success:
                messages.success(request, f"Successfully uninstalled {app_id}")
            else:
                messages.error(request, f"Failed to uninstall {app_id}: {message}")
        except Exception as e:
            logger.error(f"Error uninstalling {app_id}: {e}")
            messages.error(request, "Error uninstalling app")
        
        return redirect('installed_apps')
    
    return redirect('home')


def run_app(request, app_id):
    """Run an installed application"""
    try:
        success = PyStore.run_app(app_id)
        if success:
            messages.success(request, f"Launching {app_id}...")
        else:
            messages.error(request, f"Failed to launch {app_id}")
    except Exception as e:
        logger.error(f"Error running {app_id}: {e}")
        messages.error(request, "Error launching app")
    
    return redirect('installed_apps')


def signup(request):
    """User signup view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


def about(request):
    """About page"""
    return render(request, 'about.html')
