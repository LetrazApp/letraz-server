# CircleCI Configuration for Letraz Server

## Required Environment Variables

Set up the following environment variables in CircleCI project settings:

1. **SSH_USER**: Username for SSH access to your DigitalOcean droplet
2. **SSH_HOST**: IP address of your DigitalOcean droplet
3. **SSH_KEY_FINGERPRINT**: Fingerprint of the SSH key registered in CircleCI
4. **DOCKER_USERNAME**: Your Docker Hub username
5. **DOCKER_PASSWORD**: Your Docker Hub password

## Setting Up SSH Keys

1. Generate an SSH key pair on your local machine:
   ```
   ssh-keygen -t ed25519 -C "circleci-deploy-key"
   ```

2. Add the public key to your DigitalOcean droplet's authorized_keys:
   ```
   cat ~/.ssh/id_ed25519.pub | ssh user@your-droplet-ip "cat >> ~/.ssh/authorized_keys"
   ```

3. Add the private key to CircleCI:
   - Go to Project Settings > SSH Keys > Add SSH Key
   - Paste the private key content
   - Add hostname (your droplet's IP)
   - Copy the fingerprint and set it as SSH_KEY_FINGERPRINT in environment variables

## Deployment Path Configuration

Edit the `scripts/deploy.sh` file to update the following paths:
- `/path/to/letraz-server/.env`: Path to your .env file on the droplet
- `/path/to/letraz-server/media`: Path to your media directory
- `/path/to/letraz-server/logs`: Path to your logs directory

## First-Time Setup on Droplet

1. Create required directories on your droplet:
   ```bash
   mkdir -p /path/to/letraz-server/media /path/to/letraz-server/logs
   ```

2. Copy your .env file to the droplet:
   ```bash
   scp .env user@your-droplet-ip:/path/to/letraz-server/.env
   ``` 