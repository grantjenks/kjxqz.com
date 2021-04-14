FROM nginx

WORKDIR /app

COPY www /app/www

COPY nginx.conf /etc/nginx/nginx.conf
