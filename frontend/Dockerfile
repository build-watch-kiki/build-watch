FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci --no-audit --legacy-peer-deps

COPY . .

ARG VITE_SHOW_MOCK_PROJECT
ENV VITE_SHOW_MOCK_PROJECT=$VITE_SHOW_MOCK_PROJECT

RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
