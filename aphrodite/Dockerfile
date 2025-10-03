## Dockerfile
################################
## BUILD ENVIRONMENT ###########
################################

# Use the official Node.js Alpine image (adjust based on your project's requirements)
# You can find the appropriate image on Docker Hub: https://hub.docker.com/_/node
# In this example, we're using node:20-alpine3.20
# run in termilnal commande line "node --version to get the version of your app"
FROM node:20-alpine3.20 As build

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json into the container
COPY package*.json pnpm-lock.yaml ./

# Install dependencies using npm
RUN npm i -g pnpm
RUN pnpm install

# Copy the project files into the working directory
COPY ./ ./

# Use .env.production for production builds, fallback to .env if it doesn't exist
RUN if [ -f .env.production ]; then cp .env.production .env; fi

# Build the React app for production
RUN pnpm build

################################
#### PRODUCTION ENVIRONMENT ####
################################

# Use the official NGINX image for production
FROM nginx:stable-alpine as production
# Environment variables will be loaded from .env file copied by COPY ./ ./

# copy nginx configuration in side conf.d folder
COPY --from=build /usr/src/app/nginx /etc/nginx/conf.d

# Copy the build output from the dist folder into the Nginx html directory
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Expose port 80 to allow access to the app
EXPOSE 80

# Run Nginx in the foreground
ENTRYPOINT ["nginx", "-g", "daemon off;"] 