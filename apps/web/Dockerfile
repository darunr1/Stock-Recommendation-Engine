FROM node:22-alpine AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile --ignore-scripts

FROM deps AS build
ARG API_UPSTREAM_URL=http://api:8000
ARG NEXT_PUBLIC_APP_BASE_URL=http://localhost:3000
ENV API_UPSTREAM_URL=$API_UPSTREAM_URL NEXT_PUBLIC_APP_BASE_URL=$NEXT_PUBLIC_APP_BASE_URL
COPY apps/web apps/web
RUN pnpm --filter @equity-lens/web build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
WORKDIR /app
RUN addgroup -S web && adduser -S web -G web
COPY --from=build --chown=web:web /app/apps/web/.next/standalone ./
COPY --from=build --chown=web:web /app/apps/web/.next/static ./apps/web/.next/static
USER web
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
