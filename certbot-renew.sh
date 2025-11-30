#!/bin/bash

# SSL Certificate Setup and Auto-renewal Script
set -e

echo "🚀 Starting SSL certificate setup for mart.ktsf.ru..."

# Create necessary directories for Certbot
mkdir -p ./certbot_www
mkdir -p ./certbot_data

echo "1. Testing domain accessibility..."
if ping -c 1 mart.ktsf.ru &> /dev/null; then
    echo "✅ Domain mart.ktsf.ru is resolvable"
else
    echo "❌ Domain mart.ktsf.ru is not resolvable. Please check DNS settings."
    exit 1
fi

echo "2. Starting all services (waiting for web to be healthy)..."
docker-compose up -d db redis web

echo "3. Waiting for web service to be healthy..."
# Ждем пока web сервис станет здоровым
for i in {1..30}; do
    if docker-compose ps web | grep -q "(healthy)"; then
        echo "✅ Web service is healthy!"
        break
    else
        echo "⏳ Waiting for web service to be healthy... ($i/30)"
        sleep 5
    fi
done

echo "4. Starting nginx..."
docker-compose up -d nginx

echo "5. Waiting for nginx to start..."
sleep 10

echo "6. Testing HTTP access to domain..."
if curl -f -m 10 http://mart.ktsf.ru/ > /dev/null 2>&1; then
    echo "✅ HTTP access is working"
else
    echo "⚠️ HTTP access test failed, but continuing..."
fi

echo "7. Testing ACME challenge path..."
mkdir -p ./certbot_www/.well-known/acme-challenge/
echo "test" > ./certbot_www/.well-known/acme-challenge/test.txt

if curl -f -m 10 http://mart.ktsf.ru/.well-known/acme-challenge/test.txt > /dev/null 2>&1; then
    echo "✅ ACME challenge path is accessible"
    rm ./certbot_www/.well-known/acme-challenge/test.txt
else
    echo "❌ ACME challenge path is not accessible"
    docker-compose logs nginx
    exit 1
fi

echo "8. Obtaining SSL certificate from Let's Encrypt..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    -d mart.ktsf.ru \
    --email admin@mart.ktsf.ru \
    --agree-tos \
    --no-eff-email \
    --non-interactive || {
    echo "❌ Certificate issuance failed"
    exit 1
}

echo "✅ Certificate obtained successfully!"

echo "9. Setting up automatic renewal..."
CRON_JOB="0 3 * * * cd /root/ad_service && docker-compose run --rm certbot renew --quiet && docker-compose exec nginx nginx -s reload"

if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Automatic renewal cron job installed"
else
    echo "✅ Automatic renewal cron job already exists"
fi

echo "10. Testing SSL configuration..."
docker-compose exec nginx nginx -t && echo "✅ SSL configuration test passed"

echo "11. Testing HTTPS access..."
sleep 5
if curl -f -k -m 10 https://mart.ktsf.ru/ > /dev/null 2>&1; then
    echo "✅ HTTPS is working!"
else
    echo "⚠️ HTTPS test failed, but certificate was issued"
fi

echo ""
echo "🎉 SSL setup completed successfully!"
echo "🔐 Your site is now available at: https://mart.ktsf.ru"
echo "🔄 Certificate will be automatically renewed every 3 months"