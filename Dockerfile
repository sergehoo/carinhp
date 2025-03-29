FROM python:3.9-slim
LABEL authors="ogahserge"

WORKDIR /epidemietrackr-app
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Install system dependencies including g++ and GDAL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    software-properties-common \
    ca-certificates \
    dirmngr \
    gnupg2 \
    lsb-release \
    postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt /epidemietrackr-app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /epidemietrackr-app/

# Expose port 8000
EXPOSE 8000

# Start the application using Gunicorn
CMD ["gunicorn", "epidemietrackr.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]


#FROM python:3.9-slim
#LABEL authors="ogahserge"
#
#ENV DJANGO_SETTINGS_MODULE=epidemietrackr.settings
#
#WORKDIR /epidemietrackr-app
#
#COPY requirements.txt /epidemietrackr-app/requirements.txt
#
## Installer les dépendances système nécessaires pour GDAL et PostgreSQL
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends \
#    gdal-bin \
#    libgdal-dev \
#    libpq-dev \
#    gcc \
#    && apt-get clean && \
#    rm -rf /var/lib/apt/lists/*
#
## Définir la variable d'environnement pour GDAL
#ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
#ENV C_INCLUDE_PATH=/usr/include/gdal
#ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
## Installer les dépendances Python
#RUN pip install --no-cache-dir -r requirements.txt
#
#COPY . /epidemietrackr-app/
#
## Exposer le port sur lequel l'application Django sera accessible
#EXPOSE 8000
#RUN python3 manage.py migrate
## Démarrer l'application
#CMD ["./wait-for-it.sh", "epidemietrackrDB:5432", "--","gunicorn", "epidemietrackr.wsgi:application", "--bind=0.0.0.0:8000"]
#
#
#ENV DJANGO_SETTINGS_MODULE=epidemietrackr.settings

#-----------------------------------------------------------------------------------------------------------------------------------
#FROM python:3.9-slim
#LABEL authors="ogahserge"
#
##ENV DJANGO_SETTINGS_MODULE=epidemietrackr.settings
#
#WORKDIR /epidemietrackr-app
#ENV VIRTUAL_ENV=/opt/venv
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"
## set environment variables
##ENV PYTHONDONTWRITEBYTECODE 1
##ENV PYTHONUNBUFFERED 1
#RUN pip install --upgrade pip
#COPY requirements.txt /epidemietrackr-app/requirements.txt
#
## Installer les dépendances système nécessaires pour GDAL et PostgreSQL
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends \
#    gdal-bin \
#    libgdal-dev \
#    libpq-dev \
#    gcc \
#    && apt-get clean && \
#    rm -rf /var/lib/apt/lists/*
#
## Définir la variable d'environnement pour GDAL
#ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
#ENV C_INCLUDE_PATH=/usr/include/gdal
#ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
## Installer les dépendances Python
#RUN pip install --no-cache-dir -r requirements.txt
#
#COPY . /epidemietrackr-app/
#
#RUN apt-get update && apt-get install -y postgresql-client
## Exposer le port sur lequel l'application Django sera accessible
#EXPOSE 8000
#
## Démarrer l'application
##CMD ["gunicorn", "epidemietrackr.wsgi:application", "--bind=0.0.0.0:8000"]
#CMD ["gunicorn", "epidemietrackr.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]
##CMD ["gunicorn", "epidemietrackr.wsgi:application", "--bind=0.0.0.0:8000", "--timeout=180", "--log-level=debug"]