FROM node:18-alpine AS development

WORKDIR /app

# Instalar curl para healthcheck
RUN apk add --no-cache curl

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ /app/

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
