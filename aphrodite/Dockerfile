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
ENV VITE_API_URL=https://chat.lexin.cs.ui.ac.id
ENV VITE_SUPABASE_URL=https://fxapohscvuvrkucwmooz.supabase.co
ENV VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4YXBvaHNjdnV2cmt1Y3dtb296Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc0MzU4NjEsImV4cCI6MjA1MzAxMTg2MX0.fg4KKyp9-ufSHEb9ato-NkrqbMLllD-K9xYrPchY9XM        

# Build the React app for production
RUN pnpm build

################################
#### PRODUCTION ENVIRONMENT ####
################################

# Use the official NGINX image for production
FROM nginx:stable-alpine as production
ENV VITE_API_URL=https://chat.lexin.cs.ui.ac.id
ENV VITE_SUPABASE_URL=https://fxapohscvuvrkucwmooz.supabase.co
ENV VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4YXBvaHNjdnV2cmt1Y3dtb296Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc0MzU4NjEsImV4cCI6MjA1MzAxMTg2MX0.fg4KKyp9-ufSHEb9ato-NkrqbMLllD-K9xYrPchY9XM        

# copy nginx configuration in side conf.d folder
COPY --from=build /usr/src/app/nginx /etc/nginx/conf.d

# Copy the build output from the dist folder into the Nginx html directory
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Expose port 80 to allow access to the app
EXPOSE 80

# Run Nginx in the foreground
ENTRYPOINT ["nginx", "-g", "daemon off;"] 