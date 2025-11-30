#!/bin/bash

# Script for obtaining and renewing SSL certificates
set -e

echo "🚀 Starting SSL certificate setup..."

# Create necessary directories
mkdir -p certbot_www
mkdir -p certbot_data

# Start nginx temporarily for initial certificate issuance
echo "Starting nginx for initial certificate setup..."
docker-compose up -d nginx

# Wait for nginx to start
sleep 10

# Obtain the initial certificate
echo "Obtaining SSL certificate from Let's Encrypt..."
docker-compose run --rm certbot

# Stop nginx
echo "Stopping nginx..."
docker-compose down

# Start all services with SSL
echo "Starting all services with SSL..."
docker-compose up -d

echo "✅ SSL certificate setup completed!"
echo "🔧 Certificate will be automatically renewed"

# Add cron job for automatic renewal
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/docker-compose -f /root/ad_service/docker-compose.yml run --rm certbot renew --quiet && /usr/bin/docker-compose -f /root/ad_service/docker-compose.yml exec nginx nginx -s reload") | crontab -

echo "✅ Automatic renewal cron job installed!"