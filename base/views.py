from django.shortcuts import render, redirect, get_object_or_404
from .utils import PyStore
from django.utils import timezone


def home(request):
    if request.method == 'POST':
        app_name = request.POST.get('app_name', '')
        if app_name.lower() == 'quit':
            return redirect('home')
        
        # Perform search
        search_results = PyStore.flatpak_search(app_name)
        return render(request, 'results.html', {
            'app_name': app_name,
            'search_results': search_results
        })
    
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


    
# views.py
from django.http import JsonResponse
import json
import time
from threading import Thread
from .utils import PyStore
from django.http import JsonResponse
import json
import time
from threading import Thread
from .utils import PyStore

installation_progress = {}


def install(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '')
        if app_id.lower() == 'quit':
            return redirect('home')
        
        install_id = f"{app_id}_{int(time.time())}"
        
        # Initialize progress immediately with basic info
        installation_progress[install_id] = {
            'status': 'initializing',
            'progress': 5,  # Start at 5% to show immediate activity
            'message': 'Preparing installation...',
            'app_id': app_id,
            'logs': []
        }
        
        def install_thread():
            try:
                # Phase 1: Preparation (fast)
                installation_progress[install_id].update({
                    'progress': 10,
                    'message': 'Checking dependencies...'
                })
                
                # Phase 2: Download (simulate progress)
                def progress_callback(output):
                    installation_progress[install_id]['logs'].append(output)
                    
                    current_progress = installation_progress[install_id]['progress']
                    
                    if 'Percentage:' in output:
                        try:
                            percent = int(output.split('Percentage:')[1].split('%')[0].strip())
                            # Scale download to 10-70% of total progress
                            scaled_percent = 10 + (percent * 0.6)
                            # Only update if progress increased
                            if scaled_percent > current_progress:
                                installation_progress[install_id]['progress'] = scaled_percent
                                installation_progress[install_id]['message'] = f'Downloading ({percent}%)...'
                        except:
                            pass
                    elif 'Installing' in output:
                        if current_progress < 70:
                            installation_progress[install_id].update({
                                'progress': 70,
                                'message': 'Installing files...'
                            })
                    elif 'Finishing' in output:
                        if current_progress < 90:
                            installation_progress[install_id].update({
                                'progress': 90,
                                'message': 'Finalizing installation...'
                            })
                
                # Run installation with the existing progress_callback
                success, message = PyStore.install_app_with_progress(app_id, progress_callback)
                
                if success:
                    installation_progress[install_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Installation complete!'
                    })
                else:
                    installation_progress[install_id].update({
                        'status': 'failed',
                        'progress': 100,  # Show full bar even on failure
                        'message': f'Installation failed: {message}'
                    })
                
            except Exception as e:
                installation_progress[install_id].update({
                    'status': 'failed',
                    'message': f'Error: {str(e)}',
                    'progress': 100
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
        'logs': []
    })
    
    # Add estimated time remaining (simple calculation)
    if progress_data['status'] == 'running':
        remaining = (100 - progress_data['progress']) / 2  # Simple estimation (2% per second)
        progress_data['eta'] = f"{int(remaining)} seconds remaining"
    
    return JsonResponse(progress_data)

def installation_progress_view(request, install_id):
    return render(request, 'installation_progress.html', {'install_id': install_id})

# def get_installation_progress(request, install_id):
#     progress_data = installation_progress.get(install_id, {
#         'status': 'unknown',
#         'progress': 0,
#         'message': 'Installation not found',
#         'app_id': '',
#         'logs': []
#     })
#     return JsonResponse(progress_data)

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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import InstalledApp
from .utils import PyStore

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
    app_info = PyStore.get_app_info(app_id)
    
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


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

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