# platform/frontend/Dockerfile
#
# STATUS: written, not built — no local Docker or Node.js install (see
# ROADMAP.md "Known blockers"). This is the least-validated artifact in
# the platform layer: not even `npm install`/`tsc`/`eslint` has run
# against this code, since Node isn't available on this machine either
# (same no-admin-rights story as everything Homebrew-gated).

FROM node:22-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]
