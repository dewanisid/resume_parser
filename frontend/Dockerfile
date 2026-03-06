FROM node:20-alpine

WORKDIR /app

# Copy package files first — Docker caches this layer.
# If package.json hasn't changed, npm ci is skipped on rebuild.
COPY package*.json ./
RUN npm ci

# Source code is NOT copied here — it's mounted as a volume in docker-compose
# so that edits on your laptop are reflected in the container instantly (hot reload).

EXPOSE 5173

# --host makes Vite listen on 0.0.0.0 (all interfaces), not just 127.0.0.1.
# Without this, the port is only accessible inside the container.
CMD ["npm", "run", "dev", "--", "--host"]
