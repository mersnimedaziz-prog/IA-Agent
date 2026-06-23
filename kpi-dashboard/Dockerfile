# Stage 1: Build the Angular application
FROM node:20 AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copy the rest of the application source code
COPY . .

# Build the Angular app for SSR (production)
RUN npm run build

# Stage 2: Serve the application using Node.js (SSR)
FROM node:20-alpine

WORKDIR /app

# Copy the built artifacts from the build stage
COPY --from=build /app/dist/kpi-dashboard ./dist/kpi-dashboard

# Copy package.json for the start script
COPY package.json ./

# Expose the port the app runs on (Angular SSR defaults to 4000)
EXPOSE 4000

# Command to run the SSR application
CMD ["node", "dist/kpi-dashboard/server/server.mjs"]
