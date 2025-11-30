# Deployment to Fly.io

This guide explains how to deploy the Eidos Geometry Service to Fly.io.

## Prerequisites

1. Install the Fly.io CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Sign up for a Fly.io account: https://fly.io/app/sign-up/
3. Login to Fly.io: `fly auth login`

## Initial Deployment

1. **Initialize Fly.io app** (first time only):
   ```bash
   fly launch
   ```
   - This will create a `fly.toml` file (already created)
   - Choose a region close to your users
   - Don't deploy yet if prompted

2. **Deploy the application**:
   ```bash
   fly deploy
   ```

3. **Check deployment status**:
   ```bash
   fly status
   ```

4. **View logs**:
   ```bash
   fly logs
   ```

## Configuration

### Environment Variables

If you need to set environment variables:
```bash
fly secrets set KEY=value
```

### Scaling

Scale the application:
```bash
# Scale to 1 instance (always running)
fly scale count 1

# Scale to 0 instances (auto-start on request)
fly scale count 0
```

### Regions

List available regions:
```bash
fly regions list
```

Add a region:
```bash
fly regions add <region-code>
```

## Health Check

The service includes a health check endpoint at `/health`. Fly.io can use this for health checks.

## Monitoring

- View app metrics: `fly dashboard`
- View logs: `fly logs`
- SSH into the machine: `fly ssh console`

## Troubleshooting

- Check logs: `fly logs`
- View app info: `fly status`
- Restart the app: `fly apps restart <app-name>`
- Check machine status: `fly machine list`

## Updating

To update the application:
```bash
fly deploy
```

This will build a new Docker image and deploy it.

