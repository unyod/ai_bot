#!/bin/sh
set -eu

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.example and set DOMAIN and CERTBOT_EMAIL first." >&2
  exit 1
fi

set -a
. ./.env
set +a

if [ -z "${DOMAIN:-}" ] || [ -z "${CERTBOT_EMAIL:-}" ]; then
  echo "DOMAIN and CERTBOT_EMAIL must be set in .env." >&2
  exit 1
fi

if [ "${STAGING:-0}" = "1" ]; then
  staging_arg="--staging"
else
  staging_arg=""
fi

data_path="./certbot/conf"
webroot_path="./certbot/www"
rsa_key_size=4096

mkdir -p "$data_path/live/$DOMAIN" "$webroot_path"

if [ ! -e "$data_path/live/$DOMAIN/fullchain.pem" ]; then
  echo "Creating temporary certificate so Nginx can start."
  docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
    openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
    -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
    -out "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
    -subj "/CN=localhost"
fi

docker compose -f docker-compose.prod.yml up -d nginx
docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot \
  $staging_arg --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email \
  -d "$DOMAIN"

docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
echo "Certificate setup completed for $DOMAIN."

