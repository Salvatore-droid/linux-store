from django.shortcuts import render, redirect
from .utils import PyStore

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

def install(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '')
        if app_id.lower() == 'quit':
            return redirect('home')
        
        # Install the app
        success, message = PyStore.install_app(app_id)
        if success:
            # Run the app after installation
            PyStore.run_app(app_id)
            return render(request, 'results.html', {
                'message': f"Successfully installed and launched {app_id}",
                'installed': True
            })
        else:
            return render(request, 'results.html', {
                'error': f"Failed to install {app_id}: {message}"
            })
    
    return redirect('home')

def check_flatpak(request):
    if not PyStore.check_flatpak():
        results = PyStore.install_flatpak()
        return render(request, 'results.html', {
            'flatpak_install': True,
            'install_results': results
        })
    return redirect('home')