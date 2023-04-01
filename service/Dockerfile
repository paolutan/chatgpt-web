# service
FROM node:lts-alpine

COPY /service /app

WORKDIR /app
RUN apk add --no-cache git \
    && npm install pnpm@7.30.5 -g \
    && pnpm install --only=production \
    && rm -rf /root/.npm /root/.pnpm-store /usr/local/share/.cache /tmp/*


EXPOSE 3002

CMD ["pnpm", "run", "start"]
