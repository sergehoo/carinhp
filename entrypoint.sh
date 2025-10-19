#!/bin/sh
set -e

# Vérifs simples
echo "⏳ Attente de la base de données..."
: "${DATABASE_HOST:=rageDB}"
: "${DATABASE_USER:?DATABASE_USER manquant}"
: "${DATABASE_NAME:?DATABASE_NAME manquant}"

until pg_isready -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME"; do
  sleep 2
done
echo "✅ Base de données disponible"

# Migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecte statiques
#echo "🎨 Collecte des statiques..."
#python manage.py collectstatic --noinput

# Lancer la commande finale (Gunicorn/Daphne passée par CMD)
echo "🚀 Lancement: $@"
exec "$@"