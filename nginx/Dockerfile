# build front-end
FROM node:lts-alpine AS builder

WORKDIR /chatgpt-web
COPY ./ /chatgpt-web
ENV VITE_GLOB_API_URL /api
ENV VITE_APP_API_BASE_URL http://localhost:3002/
ENV VITE_GLOB_OPEN_LONG_REPLY false

RUN npm install pnpm -g && pnpm install && pnpm run build

# nginx
FROM nginx:alpine

ENV TZ=Asia/Shanghai

COPY --from=builder /chatgpt-web/dist /usr/share/nginx/html

CMD [ "nginx", "-g", "daemon off;" ]
