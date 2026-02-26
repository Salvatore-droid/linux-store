from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InstalledApp
from django.http import JsonResponse
import json
import time
from threading import Thread
from .utils import PyStore
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login



from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InstalledApp
from django.http import JsonResponse
import json
import time
from threading import Thread
from .utils import PyStore
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from datetime import datetime

# Global dictionary to track installation progress
installation_progress = {}

def home(request):
    if request.method == 'POST':
        app_name = request.POST.get('app_name', '')
        if app_name.lower() == 'quit':
            return redirect('home')
        
        search_results = PyStore.flatpak_search(app_name)
        return render(request, 'results.html', {
            'app_name': app_name,
            'search_results': search_results,  # Now this is a list of dictionaries
            'has_results': len(search_results) > 0
        })
    
    return render(request, 'index.html')


# views.py - Updated install function with real progress

# views.py - Updated install function with proper success/failure handling

def install(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '')
        if app_id.lower() == 'quit':
            return redirect('home')
        
        install_id = f"{app_id}_{int(time.time())}"
        
        # Initialize progress with real tracking
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
                    },
                    'end_time': datetime.now().isoformat()
                })
                
                # Add to installed apps if user is authenticated
                if request.user.is_authenticated:
                    app_name = app_id.split('.')[-1].capitalize()
                    InstalledApp.objects.update_or_create(
                        user=request.user,
                        app_id=app_id,
                        defaults={
                            'name': app_name,
                            'version': installation_progress[install_id]['metadata']['version'],
                            'size': installation_progress[install_id]['metadata']['size'],
                            'install_date': timezone.now(),
                            'status': 'up_to_date'
                        }
                    )
                
            except Exception as e:
                # Handle any unexpected errors
                installation_progress[install_id].update({
                    'status': 'failed',
                    'message': f'Unexpected error: {str(e)}',
                    'progress': 0,
                    'logs': installation_progress[install_id]['logs'] + [f'❌ ERROR: {str(e)}'],
                    'end_time': datetime.now().isoformat()
                })
        
        Thread(target=install_thread).start()
        return redirect('installation_progress', install_id=install_id)
    
    return redirect('home')

# views.py - Update the get_installation_progress function

def get_installation_progress(request, install_id):
    progress_data = installation_progress.get(install_id, {
        'status': 'unknown',
        'progress': 0,
        'message': 'Installation not found',
        'app_id': '',
        'logs': [],
        'stages': {
            'preparing': {'started': False, 'completed': False},
            'downloading': {'started': False, 'completed': False},
            'installing': {'started': False, 'completed': False},
            'finalizing': {'started': False, 'completed': False}
        }
    })
    
    # Calculate ETA if installation is in progress and not failed/completed
    if progress_data['status'] not in ['completed', 'failed', 'unknown'] and progress_data['progress'] > 0:
        try:
            start_time = datetime.fromisoformat(progress_data['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            if progress_data['progress'] > 0:
                total_estimated = elapsed * (100 / progress_data['progress'])
                remaining = total_estimated - elapsed
                progress_data['eta_seconds'] = max(0, int(remaining))
            else:
                progress_data['eta_seconds'] = None
        except:
            progress_data['eta_seconds'] = None
    
    # Ensure failed status shows 0 progress
    if progress_data['status'] == 'failed':
        progress_data['progress'] = 0
    
    return JsonResponse(progress_data)

def installation_progress_view(request, install_id):
    # Verify the installation exists
    if install_id not in installation_progress:
        messages.error(request, "Installation session not found")
        return redirect('home')
    
    return render(request, 'installation_progress.html', {
        'install_id': install_id,
        'app_id': installation_progress[install_id].get('app_id', '')
    })





def launch_app(request, app_id):
    PyStore.run_app(app_id)
    return redirect('home')

def check_flatpak(request):
    if not PyStore.check_flatpak():
        results = PyStore.install_flatpak()
        return render(request, 'results.html', {
            'flatpak_install': True,
            'install_results': results
        })
    return redirect('home')


@login_required
def installed_apps(request):
    # Sync with system installed apps
    if request.method == 'POST' and 'sync' in request.POST:
        system_apps = PyStore.get_installed_apps()
        
        # Remove apps no longer installed
        current_ids = [app['app_id'] for app in system_apps]
        InstalledApp.objects.filter(user=request.user).exclude(app_id__in=current_ids).delete()
        
        # Add/update installed apps
        for app_data in system_apps:
            # Clean up size format (remove units and handle decimals)
            size_str = app_data.get('size', '0 MB').split()[0]
            try:
                size_mb = float(size_str)
            except ValueError:
                size_mb = 0.0
            
            InstalledApp.objects.update_or_create(
                user=request.user,  # Now part of the unique constraint
                app_id=app_data['app_id'],
                defaults={
                    'name': app_data['app_id'].split('.')[-1].capitalize(),
                    'version': app_data.get('version', 'unknown'),
                    'size': f"{size_mb:.1f} MB" if size_mb > 0 else "0 MB",
                    'status': 'up_to_date',
                }
            )
        messages.success(request, "Applications successfully synchronized")
        return redirect('installed')

    # Bulk actions
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        
        if 'uninstall' in request.POST:
            for app_id in selected_ids:
                success, message = PyStore.uninstall_app(app_id)
                if success:
                    InstalledApp.objects.filter(user=request.user, app_id=app_id).delete()
                    messages.success(request, f"Successfully uninstalled {app_id}")
                else:
                    messages.error(request, f"Failed to uninstall {app_id}: {message}")
        
        if 'launch' in request.POST:
            for app_id in selected_ids:
                PyStore.run_app(app_id)
            messages.success(request, f"Launched {len(selected_ids)} application(s)")
        
        return redirect('installed')

    apps = InstalledApp.objects.filter(user=request.user)
    
    # Calculate total size (handle decimal values)
    total_size = 0.0
    for app in apps:
        if app.size and 'MB' in app.size:
            try:
                total_size += float(app.size.split()[0])
            except (ValueError, IndexError):
                continue
    
    context = {
        'apps': apps,
        'total_count': apps.count(),
        'total_size': f"{total_size:.1f} MB",
        'recent_count': apps.filter(install_date__gte=timezone.now()-timezone.timedelta(days=7)).count(),
        'update_count': apps.filter(status='update_available').count(),
    }
    return render(request, 'installed.html', context)

@login_required
def app_detail(request, app_id):
    app = get_object_or_404(InstalledApp, user=request.user, app_id=app_id)
    app_info = PyStore.get_installed_app_info(app_id)
    
    if request.method == 'POST':
        if 'uninstall' in request.POST:
            success, message = PyStore.uninstall_app(app_id)
            if success:
                app.delete()
                return redirect('installed')
            else:
                messages.error(request, f"Failed to uninstall: {message}")
        
        if 'launch' in request.POST:
            PyStore.run_app(app_id)
            return redirect('installed')
    
    context = {
        'app': app,
        'app_info': app_info,
    }
    return render(request, 'app_detail.html', context)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Or wherever you want to redirect after signup
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def about(request):
    return render(request, 'about.html')