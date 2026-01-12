# ZeroPhi API Deployment Guide

This guide explains how to deploy the ZeroPhi API in various environments with configurable settings.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e .

# Run with default settings (localhost:8000)
python -m zerophix.api.rest

# Or with custom settings
ZEROPHIX_API_HOST=0.0.0.0 ZEROPHIX_API_PORT=8080 python -m zerophix.api.rest
```

### Using Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration

3. Run the API:
```bash
python -m zerophix.api.rest
```

## Configuration Methods

The API can be configured in three ways (in order of precedence):

1. **Environment Variables** (highest priority) - See [.env.example](.env.example)
2. **YAML Configuration** - See [configs/api_config.yml](configs/api_config.yml)
3. **Default Values** (lowest priority) - Defined in `src/zerophix/config.py`

## Key Configuration Options

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ZEROPHIX_API_HOST` | `127.0.0.1` | Host to bind to (`0.0.0.0` for all interfaces) |
| `ZEROPHIX_API_PORT` | `8000` | Port to bind to |
| `ZEROPHIX_API_WORKERS` | `1` | Number of worker processes |
| `ZEROPHIX_API_RELOAD` | `false` | Auto-reload on code changes |

### CORS Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ZEROPHIX_CORS_ENABLED` | `true` | Enable CORS middleware |
| `ZEROPHIX_CORS_ORIGINS` | `*` | Allowed origins (comma-separated) |
| `ZEROPHIX_CORS_CREDENTIALS` | `true` | Allow credentials |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ZEROPHIX_REQUIRE_AUTH` | `false` | Require API key authentication |
| `ZEROPHIX_API_KEYS` | `` | Valid API keys (comma-separated) |

### SSL/TLS Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ZEROPHIX_SSL_ENABLED` | `false` | Enable SSL/TLS |
| `ZEROPHIX_SSL_KEYFILE` | - | Path to SSL private key |
| `ZEROPHIX_SSL_CERTFILE` | - | Path to SSL certificate |

## Deployment Scenarios

### 1. Local Development

```bash
# .env
ZEROPHIX_API_HOST=127.0.0.1
ZEROPHIX_API_PORT=8000
ZEROPHIX_API_RELOAD=true
ZEROPHIX_ENV=development
ZEROPHIX_LOG_LEVEL=debug
ZEROPHIX_DOCS_ENABLED=true
```

```bash
python -m zerophix.api.rest
```

Access at: http://localhost:8000/docs

### 2. Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["python", "-m", "zerophix.api.rest"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ZEROPHIX_API_HOST=0.0.0.0
      - ZEROPHIX_API_PORT=8000
      - ZEROPHIX_ENV=production
      - ZEROPHIX_REQUIRE_AUTH=true
      - ZEROPHIX_API_KEYS=${API_KEYS}
      - ZEROPHIX_CORS_ORIGINS=https://app.example.com
      - ZEROPHIX_DOCS_ENABLED=false
```

Run:
```bash
docker-compose up
```

### 3. Production Server (with Nginx)

**1. Run the API:**
```bash
# .env
ZEROPHIX_API_HOST=127.0.0.1
ZEROPHIX_API_PORT=8000
ZEROPHIX_API_WORKERS=4
ZEROPHIX_ENV=production
ZEROPHIX_REQUIRE_AUTH=true
ZEROPHIX_PROXY_HEADERS=true
ZEROPHIX_DOCS_ENABLED=false
```

**2. Configure Nginx as reverse proxy:**
```nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**3. Run with systemd:**
```ini
# /etc/systemd/system/zerophi-api.service
[Unit]
Description=ZeroPhi API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/zerophi
Environment="PATH=/opt/zerophi/venv/bin"
EnvironmentFile=/opt/zerophi/.env
ExecStart=/opt/zerophi/venv/bin/python -m zerophix.api.rest
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl enable zerophi-api
sudo systemctl start zerophi-api
```

### 4. AWS Elastic Beanstalk

**1. Create `.ebextensions/zerophi.config`:**
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    ZEROPHIX_API_HOST: "0.0.0.0"
    ZEROPHIX_API_PORT: "8000"
    ZEROPHIX_ENV: "production"
    ZEROPHIX_PROXY_HEADERS: "true"
    ZEROPHIX_REQUIRE_AUTH: "true"
```

**2. Deploy:**
```bash
eb init -p python-3.9 zerophi-api
eb create zerophi-api-env
eb setenv ZEROPHIX_API_KEYS="your-secret-key"
eb deploy
```

### 5. Google Cloud Run

**1. Create Dockerfile** (see Docker section above)

**2. Build and deploy:**
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/zerophi-api

# Deploy to Cloud Run
gcloud run deploy zerophi-api \
  --image gcr.io/PROJECT_ID/zerophi-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ZEROPHIX_API_HOST=0.0.0.0,ZEROPHIX_API_PORT=8080,ZEROPHIX_ENV=production
```

### 6. Kubernetes

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerophi-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zerophi-api
  template:
    metadata:
      labels:
        app: zerophi-api
    spec:
      containers:
      - name: api
        image: zerophi-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ZEROPHIX_API_HOST
          value: "0.0.0.0"
        - name: ZEROPHIX_API_PORT
          value: "8000"
        - name: ZEROPHIX_ENV
          value: "production"
        - name: ZEROPHIX_PROXY_HEADERS
          value: "true"
        - name: ZEROPHIX_API_KEYS
          valueFrom:
            secretKeyRef:
              name: zerophi-secrets
              key: api-keys
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: zerophi-api-service
spec:
  selector:
    app: zerophi-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

### 7. Heroku

**1. Create `Procfile`:**
```
web: python -m zerophix.api.rest
```

**2. Deploy:**
```bash
heroku create zerophi-api
heroku config:set ZEROPHIX_API_HOST=0.0.0.0
heroku config:set ZEROPHIX_ENV=production
heroku config:set ZEROPHIX_API_KEYS="your-secret-key"
git push heroku main
```

Note: Heroku automatically sets the `PORT` environment variable.

## SSL/TLS Configuration

### Option 1: Terminate SSL at Load Balancer/Reverse Proxy (Recommended)

Configure your load balancer (AWS ALB, GCP Load Balancer, Nginx, etc.) to handle SSL:

```bash
ZEROPHIX_SSL_ENABLED=false
ZEROPHIX_PROXY_HEADERS=true
```

### Option 2: SSL in the Application

Generate certificates (e.g., with Let's Encrypt):
```bash
sudo certbot certonly --standalone -d api.example.com
```

Configure:
```bash
ZEROPHIX_SSL_ENABLED=true
ZEROPHIX_SSL_KEYFILE=/etc/letsencrypt/live/api.example.com/privkey.pem
ZEROPHIX_SSL_CERTFILE=/etc/letsencrypt/live/api.example.com/fullchain.pem
```

## Authentication

### Enable API Key Authentication

1. Generate API keys:
```bash
openssl rand -hex 32
```

2. Configure:
```bash
ZEROPHIX_REQUIRE_AUTH=true
ZEROPHIX_API_KEYS=key1,key2,key3
```

3. Use in requests:
```bash
curl -H "Authorization: Bearer your-api-key" https://api.example.com/redact
```

## Monitoring and Health Checks

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "uptime": 3600.5,
  "cache_stats": {},
  "performance_summary": {}
}
```

### Metrics Endpoint

```bash
curl http://localhost:8000/stats
```

## Performance Tuning

### Workers

Set workers based on CPU cores:
```bash
# Formula: (2 x num_cores) + 1
ZEROPHIX_API_WORKERS=9  # For 4 cores
```

### Request Limits

```bash
ZEROPHIX_MAX_REQUEST_SIZE=52428800  # 50 MB
ZEROPHIX_TIMEOUT=300  # 5 minutes
```

### Rate Limiting

```bash
ZEROPHIX_RATE_LIMIT_ENABLED=true
ZEROPHIX_RATE_LIMIT_REQUESTS=100  # requests
ZEROPHIX_RATE_LIMIT_WINDOW=60     # seconds
```

## Troubleshooting

### API won't start

Check logs:
```bash
python -m zerophix.api.rest 2>&1 | tee api.log
```

### Port already in use

Change port:
```bash
ZEROPHIX_API_PORT=8001 python -m zerophix.api.rest
```

### CORS errors

Add your domain to allowed origins:
```bash
ZEROPHIX_CORS_ORIGINS=https://your-domain.com
```

### Authentication failing

Verify API key format:
```bash
curl -v -H "Authorization: Bearer your-api-key" http://localhost:8000/health
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Never commit `.env` files with real credentials**
3. **Rotate API keys regularly**
4. **Disable documentation in production**: `ZEROPHIX_DOCS_ENABLED=false`
5. **Use specific CORS origins**: Don't use `*` in production
6. **Enable authentication**: `ZEROPHIX_REQUIRE_AUTH=true`
7. **Keep software updated**: Regularly update dependencies
8. **Monitor logs**: Set up log aggregation and alerting
9. **Use rate limiting**: Prevent abuse
10. **Run behind a reverse proxy**: For additional security layers

## Support

For issues or questions:
- Check the [main README](README.md)
- Review [configs/api_config.yml](configs/api_config.yml) for examples
- Open an issue on GitHub
