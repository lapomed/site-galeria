"""
Configuração centralizada de variáveis de ambiente para o projeto LAPOMED.
"""
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent

# Segurança
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-hlplb31p-t8d53!#*j$ziqa*dtp*5p8dw@3t8&fzn(pe5f4r(m'
)

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Se DATABASE_URL for fornecida (Railway), usa PostgreSQL
# Senão, usa SQLite local
if DATABASE_URL:
    # Parse da URL do PostgreSQL
    # Formato: postgresql://user:password@host:port/database
    import re
    match = re.match(
        r'postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)',
        DATABASE_URL
    )
    
    if match:
        db_config = match.groupdict()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_config['name'],
                'USER': db_config['user'],
                'PASSWORD': db_config['password'],
                'HOST': db_config['host'],
                'PORT': db_config['port'],
            }
        }
    else:
        # Fallback para SQLite se o parse falhar
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # Desenvolvimento local com SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Porta do servidor
PORT = int(os.getenv('PORT', '4008'))
