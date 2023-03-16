# build front-end
FROM node:lts-alpine AS builder

COPY ./ /app
WORKDIR /app

RUN npm install pnpm -g && pnpm install && pnpm run build

# nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
