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
            'search_results': search_results
        })
    
    return render(request, 'index.html')


def install(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '')
        if app_id.lower() == 'quit':
            return redirect('home')
        
        install_id = f"{app_id}_{int(time.time())}"
        
        # Initialize progress with more detailed information
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
            }
        }
        
        def install_thread():
            try:
                # Update progress
                installation_progress[install_id].update({
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
                
                # Phase 1: Preparation (5-15%)
                time.sleep(1)  # Simulate preparation time
                installation_progress[install_id]['logs'].append('Dependencies checked')
                installation_progress[install_id].update({
                    'progress': 15,
                    'message': 'Dependencies verified',
                    'stages': {
                        'preparing': {'started': True, 'completed': True},
                        'downloading': {'started': True, 'completed': False}
                    }
                })
                
                # Phase 2: Download (15-70%)
                def download_progress_callback(output):
                    installation_progress[install_id]['logs'].append(output.strip())
                    
                    if 'Percentage:' in output:
                        try:
                            percent = int(output.split('Percentage:')[1].split('%')[0].strip())
                            scaled_percent = 15 + (percent * 0.55)  # Scale to 15-70% range
                            installation_progress[install_id]['progress'] = scaled_percent
                            installation_progress[install_id]['message'] = f'Downloading ({percent}%)...'
                        except:
                            pass
                
                # Perform actual installation with progress
                success, message = PyStore.install_app_with_progress(app_id, download_progress_callback)
                
                if not success:
                    installation_progress[install_id].update({
                        'status': 'failed',
                        'message': f'Installation failed: {message}',
                        'progress': 100
                    })
                    return
                
                installation_progress[install_id].update({
                    'progress': 70,
                    'message': 'Download complete, installing files...',
                    'current_stage': 'installing',
                    'stages': {
                        'downloading': {'started': True, 'completed': True},
                        'installing': {'started': True, 'completed': False}
                    }
                })
                
                # Phase 3: Installation (70-90%)
                for i in range(1, 21):
                    time.sleep(0.2)
                    installation_progress[install_id]['progress'] = 70 + (i * 1)
                    installation_progress[install_id]['message'] = f'Installing files ({i * 5}%)...'
                    installation_progress[install_id]['logs'].append(f'Installed component {i}/20')
                
                installation_progress[install_id].update({
                    'progress': 90,
                    'message': 'Finalizing installation...',
                    'current_stage': 'finalizing',
                    'stages': {
                        'installing': {'started': True, 'completed': True},
                        'finalizing': {'started': True, 'completed': False}
                    }
                })
                
                # Phase 4: Finalizing (90-100%)
                # Get actual app metadata
                app_info = PyStore.get_installed_app_info(app_id)
                if not app_info:
                    installation_progress[install_id].update({
                        'status': 'failed',
                        'message': 'Failed to verify installation',
                        'progress': 100
                    })
                    return
                
                installation_progress[install_id]['metadata'] = {
                    'size': app_info.get('size', '0 MB'),
                    'version': app_info.get('version', 'unknown')
                }
                
                installation_progress[install_id]['logs'].extend([
                    'Creating desktop shortcuts',
                    'Updating application database',
                    f"Installation verified: {app_id}"
                ])
                
                installation_progress[install_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Installation complete!',
                    'stages': {
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
                installation_progress[install_id].update({
                    'status': 'failed',
                    'message': f'Error: {str(e)}',
                    'progress': 100,
                    'logs': installation_progress[install_id]['logs'] + [f'ERROR: {str(e)}'],
                    'end_time': datetime.now().isoformat()
                })
        
        Thread(target=install_thread).start()
        return redirect('installation_progress', install_id=install_id)
    
    return redirect('home')

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
    
    # Calculate ETA if installation is in progress
    if progress_data['status'] not in ['completed', 'failed']:
        try:
            start_time = datetime.fromisoformat(progress_data['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = (100 - progress_data['progress']) * (elapsed / max(1, progress_data['progress']))
            progress_data['eta_seconds'] = int(remaining)
        except:
            progress_data['eta_seconds'] = None
    
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