FROM caddy:2.7.6-alpine

COPY ./docker/prod/Caddyfile /etc/caddy/Caddyfile
