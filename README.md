# Chat Monorepo

This monorepo contains all microservices and components for our chat application system.

## Overview

This repository is organized as a monolith repository (monorepo) containing multiple independent services. Each service resides in its own directory at the root level, with its own dependencies, configuration, and deployment process.

## Architecture

The application follows a microservices architecture pattern with the following main components:

- **Service Directory Structure**: Each service has its own directory at the root level
- **Automated Deployment**: Changes to services trigger Docker image builds and deployment
- **Centralized Configuration**: Environment variables managed through GitHub Secrets

## Key Components

### 📁 Directory Structure

```
chat-monorepo/
├── chronos/          # Real-time messaging service
├── hermes/           # Message delivery and routing service
├── pandora/          # Configuration and build metadata
│   ├── *.md5         # Checksums for each service directory
│   └── __build__     # List of services that need rebuilding
├── .github/
│   └── workflows/    # CI/CD pipelines
└── .husky/           # Git hooks
```

### 🔄 Build and Deployment System

The repository uses a custom build tracking system:

1. **Pre-commit Hook**: Calculates checksums for each service directory
   - Compares with previous checksums (stored in `.md5` files)
   - Records changed services in `pandora/__build__`

2. **GitHub Actions Workflow**:
   - Reads the `pandora/__build__` file
   - Builds Docker images for changed services
   - Pushes images to Docker Hub with tags matching service names
   - Deploys to the production environment

3. **Environment Variables**:
   - Stored in GitHub Secrets with naming pattern `SERVICENAME_ENV`
   - Deployed as `.env` files to each service directory

## Development Workflow

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/chat-monorepo.git
   cd chat-monorepo
   ```

2. Install Husky hooks:
   ```bash
   npm install
   ```

3. Work on a service:
   ```bash
   cd <service-directory>
   # Follow README instructions for the specific service
   ```

### Making Changes

1. Make changes to a service
2. Commit your changes
   - The pre-commit hook will automatically track which services changed
3. Push to main branch
   - GitHub Actions will build and deploy the changed services

### Adding a New Service

1. Create a new directory at the root level
2. Add a `Dockerfile` for the service
3. Create an empty `.md5` file in the pandora directory: `touch pandora/<service-name>.md5`
4. Add service-specific environment variables as GitHub Secret with name `<SERVICE-NAME>_ENV`

## Services

### Chronos

Real-time messaging service based on FastAPI.

- **Technology**: Python, FastAPI, AsyncIO
- **Responsibilities**: Message queuing, real-time delivery

### Hermes

Message delivery and routing service.

- **Technology**: Python
- **Responsibilities**: Message routing, delivery confirmation

## Deployment

Deployment is fully automated through GitHub Actions:

1. Changes to service code are detected by the pre-commit hook
2. When pushed to main, GitHub Actions:
   - Builds Docker images for changed services
   - Deploys the services to the production environment
   - Sets up environment variables from GitHub Secrets

## Environment Variables

Environment variables are managed through GitHub Secrets:

- For each service, create a secret named `<SERVICE-NAME>_ENV` 
- Example: `CHRONOS_ENV` for the Chronos service
- The value should contain the entire contents of the service's `.env` file