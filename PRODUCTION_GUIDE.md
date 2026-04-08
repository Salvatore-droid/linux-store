# PY-STore Production Deployment Guide

## Overview

PY-STore is a fully functional Linux application store built with Django that provides users with a seamless way to discover, search, and install Linux applications from Flathub. This guide covers deployment, configuration, and best practices for production environments.

## Features

### ✅ Fully Implemented Features

1. **Application Search & Discovery**
   - Real-time search integration with Flathub API
   - Browse thousands of Linux applications
   - Detailed app information including descriptions, categories, and ratings

2. **Application Browsing**
   - Browse all available applications with pagination
   - View app details including developer info, categories, and screenshots
   - Filter and sort applications

3. **Installation Management**
   - One-click application installation via Flatpak
   - Real-time installation progress tracking with visual indicators
   - Detailed installation logs and error reporting
   - Support for installation cancellation

4. **Installed Apps Management**
   - View all installed applications
   - Track recently added apps and available updates
   - Uninstall applications directly from the interface
   - Launch applications from the store

5. **User Interface**
   - Modern, responsive design with Tailwind CSS
   - Dark mode support
   - Mobile-friendly interface
   - Intuitive navigation

6. **Backend Integration**
   - Flathub API integration for app metadata
   - Flatpak command-line integration for installations
   - Real-time progress tracking with threading
   - Comprehensive error handling

## System Requirements

### Minimum Requirements
- Python 3.8+
- Django 4.0+
- SQLite 3.x
- Linux kernel 4.x+
- 2GB RAM
- 500MB disk space

### Recommended Requirements
- Python 3.11+
- 4GB+ RAM
- 2GB+ disk space
- Modern Linux distribution (Ubuntu 20.04+, Fedora 35+, etc.)

### Required System Packages
```bash
# Ubuntu/Debian
sudo apt-get install python3-pip python3-venv flatpak

# Fedora
sudo dnf install python3-pip python3-venv flatpak

# Arch
sudo pacman -S python-pip flatpak
```

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Salvatore-droid/linux-store.git
cd linux-store
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Django Settings
```bash
# Generate a new SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Update pystore/settings.py with your SECRET_KEY and ALLOWED_HOSTS
```

### 5. Run Migrations
```bash
python3 manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python3 manage.py createsuperuser
```

### 7. Collect Static Files
```bash
python3 manage.py collectstatic --noinput
```

### 8. Run Development Server
```bash
python3 manage.py runserver 0.0.0.0:8000
```

## Production Deployment

### Using Gunicorn

#### 1. Install Gunicorn
```bash
pip install gunicorn
```

#### 2. Create Gunicorn Configuration
Create `gunicorn_config.py`:
```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
daemon = False
```

#### 3. Run with Gunicorn
```bash
gunicorn -c gunicorn_config.py pystore.wsgi:application
```

### Using Nginx as Reverse Proxy

Create `/etc/nginx/sites-available/linux-store`:
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 100M;

    location /static/ {
        alias /path/to/linux-store/staticfiles/;
    }

    location /media/ {
        alias /path/to/linux-store/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/linux-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Using Systemd Service

Create `/etc/systemd/system/linux-store.service`:
```ini
[Unit]
Description=PY-STore Linux App Store
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/linux-store
ExecStart=/path/to/linux-store/venv/bin/gunicorn -c gunicorn_config.py pystore.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linux-store
sudo systemctl start linux-store
```

### SSL/TLS with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Update Nginx configuration to use SSL:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... rest of configuration
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```bash
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=sqlite:///db.sqlite3
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Django Settings
Update `pystore/settings.py`:
```python
# Security settings for production
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
CSRF_TRUSTED_ORIGINS = ['https://your-domain.com', 'https://www.your-domain.com']

# Database (use PostgreSQL for production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'linux_store',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}
```

## API Endpoints

### Search Applications
**Endpoint:** `POST /`
**Parameters:**
- `app_name` (string): Search query

**Response:** Rendered results page with matching applications

### Browse Applications
**Endpoint:** `GET /browse/`
**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)

**Response:** Paginated list of applications

### Application Details
**Endpoint:** `GET /app/<app_id>/`
**Parameters:**
- `app_id` (string): Application ID (e.g., `com.discordapp.Discord`)

**Response:** Detailed application information

### Install Application
**Endpoint:** `POST /install/`
**Parameters:**
- `app_id` (string): Application ID to install

**Response:** Installation progress page

### Installation Progress
**Endpoint:** `GET /api/progress/<install_id>/`
**Response:** JSON with installation progress data

### Installed Applications
**Endpoint:** `GET /installed/`
**Response:** List of installed applications

### Uninstall Application
**Endpoint:** `POST /uninstall/<app_id>/`
**Response:** Redirect to installed apps page

## Monitoring & Logging

### Application Logs
```bash
# View Gunicorn logs
sudo journalctl -u linux-store -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring
```bash
# Monitor system resources
watch -n 1 'ps aux | grep gunicorn'

# Check database size
du -sh /path/to/linux-store/db.sqlite3
```

## Troubleshooting

### Issue: Installation fails with "Flatpak not found"
**Solution:** Ensure Flatpak is installed and the Flathub remote is added:
```bash
sudo apt-get install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Issue: Search returns no results
**Solution:** Check Flathub API connectivity:
```bash
curl -X POST https://flathub.org/api/v2/search \
  -H "Content-Type: application/json" \
  -d '{"query": "discord", "limit": 5}'
```

### Issue: High memory usage
**Solution:** Adjust Gunicorn worker count in `gunicorn_config.py`:
```python
workers = 2  # Reduce from default
```

### Issue: Slow page loads
**Solution:** Enable caching and optimize database queries:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

## Security Best Practices

1. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Regular Backups**
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz /path/to/linux-store
   ```

3. **Monitor for Vulnerabilities**
   ```bash
   pip install safety
   safety check
   ```

4. **Use Strong Passwords**
   - Generate strong SECRET_KEY
   - Use strong database credentials

5. **Enable HTTPS**
   - Use SSL/TLS certificates
   - Redirect HTTP to HTTPS

6. **Rate Limiting**
   - Implement rate limiting for API endpoints
   - Use Nginx rate limiting

## Performance Optimization

1. **Database Indexing**
   ```python
   class InstalledApp(models.Model):
       app_id = models.CharField(max_length=255, db_index=True)
   ```

2. **Caching**
   - Cache popular app lists
   - Cache API responses

3. **CDN Integration**
   - Serve static files from CDN
   - Cache app icons

4. **Database Connection Pooling**
   ```bash
   pip install django-db-pool
   ```

## Backup & Recovery

### Automated Backups
Create `/usr/local/bin/backup-linux-store.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/linux-store"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz /path/to/linux-store
find $BACKUP_DIR -name "backup-*.tar.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-linux-store.sh
```

## Support & Contribution

- **Issues:** Report bugs on GitHub Issues
- **Discussions:** Join community discussions
- **Contributing:** See CONTRIBUTING.md for guidelines

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Changelog

### Version 1.0.0 (Production Release)
- ✅ Full Flathub API integration
- ✅ Real-time app search and browsing
- ✅ Installation progress tracking
- ✅ Installed apps management
- ✅ Responsive UI with Tailwind CSS
- ✅ Production-ready deployment guides

---

**Last Updated:** April 2026
**Maintained by:** Genius (Salvatore-droid)
