# build front-end
FROM node:lts-alpine AS builder

WORKDIR /chatgpt-web
COPY ./ /chatgpt-web

RUN npm install pnpm -g && pnpm install && pnpm run build

# nginx
FROM nginx:alpine

ENV TZ=Asia/Shanghai

COPY --from=builder /chatgpt-web/dist /usr/share/nginx/html

CMD [ "nginx", "-g", "daemon off;" ]
