# PY-STore - Linux Application Store

A modern, user-friendly Linux application store built with Django and powered by Flathub. Discover, search, install, and manage Linux applications with ease.

## 🎯 Features

### ✨ Core Features
- **🔍 Powerful Search**: Real-time search across thousands of Linux applications
- **📱 Browse Applications**: Explore curated collections with detailed information
- **⚡ One-Click Installation**: Install applications with a single click
- **📊 Installation Tracking**: Real-time progress monitoring with detailed logs
- **🎨 Modern UI**: Responsive design that works on desktop and mobile
- **🌐 Flathub Integration**: Access to the largest collection of Linux apps
- **📦 App Management**: Install, uninstall, and launch applications seamlessly

### 🔧 Technical Features
- Django REST framework for API endpoints
- Real-time progress tracking with threading
- Comprehensive error handling and logging
- CSRF protection and security headers
- Responsive Tailwind CSS design
- SQLite database (upgradeable to PostgreSQL)

## 📋 System Requirements

### Minimum
- Python 3.8+
- Linux kernel 4.x+
- 2GB RAM
- 500MB disk space

### Recommended
- Python 3.11+
- Ubuntu 20.04+ / Fedora 35+ / Arch Linux
- 4GB+ RAM
- 2GB+ disk space
- Flatpak installed

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Salvatore-droid/linux-store.git
cd linux-store
```

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python3 manage.py migrate
```

### 5. Run Development Server
```bash
python3 manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## 📖 Usage Guide

### Searching for Applications
1. Enter an app name in the search box (e.g., "Spotify", "Blender", "VS Code")
2. Click "Search" or press Enter
3. Browse results and click on an app for details

### Browsing Applications
1. Click "Apps" in the navigation menu
2. Browse through paginated list of applications
3. Click on any app card to view full details

### Installing Applications
1. Click "Install App" button on the app details page
2. Monitor real-time installation progress
3. View detailed logs of the installation process
4. Installation completes automatically

### Managing Installed Apps
1. Click "Installed" in the navigation menu
2. View all installed applications
3. Launch apps directly from the store
4. Uninstall apps with one click

## 🏗️ Project Structure

```
linux-store/
├── base/                          # Main Django app
│   ├── migrations/                # Database migrations
│   ├── templates/                 # HTML templates
│   │   ├── base.html             # Base template
│   │   ├── index.html            # Home page
│   │   ├── browse.html           # Browse apps
│   │   ├── app_detail.html       # App details
│   │   ├── results.html          # Search results
│   │   ├── installed.html        # Installed apps
│   │   └── installation_progress.html  # Installation tracker
│   ├── static/                    # CSS, JS, images
│   ├── admin.py                   # Django admin config
│   ├── apps.py                    # App configuration
│   ├── models.py                  # Database models
│   ├── urls.py                    # URL routing
│   ├── views.py                   # View functions
│   └── utils.py                   # Utility functions
├── pystore/                       # Django project settings
│   ├── settings.py               # Django configuration
│   ├── urls.py                   # Project URL config
│   └── wsgi.py                   # WSGI application
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
├── PRODUCTION_GUIDE.md           # Deployment guide
└── README.md                      # This file
```

## 🔌 API Endpoints

### Search Applications
```
POST /
Parameters: app_name (string)
Returns: Rendered results page
```

### Browse Applications
```
GET /browse/?page=1
Returns: Paginated application list
```

### Application Details
```
GET /app/<app_id>/
Parameters: app_id (string, e.g., com.discordapp.Discord)
Returns: Detailed app information
```

### Install Application
```
POST /install/
Parameters: app_id (string)
Returns: Installation progress page
```

### Installation Progress
```
GET /api/progress/<install_id>/
Returns: JSON progress data
```

### Installed Applications
```
GET /installed/
Returns: List of installed apps
```

### Uninstall Application
```
POST /uninstall/<app_id>/
Returns: Redirect to installed apps
```

## 🛠️ Development

### Running Tests
```bash
python3 manage.py test
```

### Creating Migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Admin Panel
```bash
python3 manage.py createsuperuser
# Then visit http://localhost:8000/admin
```

### Code Style
```bash
pip install black flake8
black .
flake8 .
```

## 📦 Dependencies

### Core
- Django 4.0+
- Python 3.8+

### API Integration
- requests (HTTP requests to Flathub API)

### Frontend
- Tailwind CSS (styling)
- Alpine.js (interactivity)

### Database
- SQLite (default)
- PostgreSQL (recommended for production)

See `requirements.txt` for complete list.

## 🚀 Production Deployment

For detailed production deployment instructions, see [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md).

### Quick Deployment with Gunicorn
```bash
pip install gunicorn
gunicorn pystore.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker (Optional)
```bash
docker build -t linux-store .
docker run -p 8000:8000 linux-store
```

## 🐛 Troubleshooting

### Issue: "Flatpak not found"
**Solution:** Install Flatpak
```bash
sudo apt-get install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Issue: Search returns no results
**Solution:** Check Flathub API connectivity
```bash
curl https://flathub.org/api/v2/search -X POST -H "Content-Type: application/json" -d '{"query":"discord"}'
```

### Issue: Installation fails
**Solution:** Check logs
```bash
python3 manage.py runserver --verbosity 3
```

### Issue: Port 8000 already in use
**Solution:** Use different port
```bash
python3 manage.py runserver 8001
```

## 📝 Configuration

### Environment Variables
Create `.env` file:
```bash
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Django Settings
Edit `pystore/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'linux_store',
    }
}
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👤 Author

**Genius (Salvatore-droid)**
- GitHub: [@Salvatore-droid](https://github.com/Salvatore-droid)

## 🙏 Acknowledgments

- [Flathub](https://flathub.org) - For providing the comprehensive app database
- [Django](https://www.djangoproject.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
- [Flatpak](https://flatpak.org/) - Application packaging

## 📞 Support

- **Issues:** Report bugs on [GitHub Issues](https://github.com/Salvatore-droid/linux-store/issues)
- **Discussions:** Join [GitHub Discussions](https://github.com/Salvatore-droid/linux-store/discussions)
- **Documentation:** See [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)

## 🗺️ Roadmap

- [ ] User accounts and favorites
- [ ] App ratings and reviews
- [ ] Automatic update notifications
- [ ] Desktop app integration
- [ ] Multi-language support
- [ ] Advanced filtering and sorting
- [ ] App recommendations
- [ ] Community contributions

## 📊 Status

**Version:** 1.0.0 (Production Ready)
**Status:** ✅ Fully Functional
**Last Updated:** April 2026

---

**Made with ❤️ for the Linux community**
