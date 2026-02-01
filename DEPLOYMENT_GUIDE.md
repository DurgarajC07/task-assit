# Production Deployment Guide

Complete guide for deploying Task Assistant AI SaaS platform to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Database Setup](#database-setup)
- [Application Deployment](#application-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Security Hardening](#security-hardening)
- [Scaling](#scaling)
- [Maintenance](#maintenance)

---

## Prerequisites

### Required Services

- **PostgreSQL 14+**: Primary database
- **Redis 7+**: Caching and rate limiting
- **Celery Workers**: Background job processing
- **Domain**: SSL-enabled domain name
- **Object Storage**: S3-compatible (optional, for file uploads)

### Required Accounts

- **Sentry**: Error tracking and monitoring
- **AI Provider API Keys**:
  - OpenAI API key
  - Anthropic API key
  - Google AI API key (optional)
  - Groq API key (optional)

### Infrastructure Requirements

**Minimum (Small Scale)**:

- **API Server**: 2 CPU, 4GB RAM
- **Worker Server**: 2 CPU, 2GB RAM
- **PostgreSQL**: 2 CPU, 4GB RAM, 50GB SSD
- **Redis**: 1 CPU, 2GB RAM

**Recommended (Production)**:

- **API Servers (2+)**: 4 CPU, 8GB RAM each
- **Worker Servers (2+)**: 4 CPU, 4GB RAM each
- **PostgreSQL**: 4 CPU, 8GB RAM, 200GB SSD
- **Redis**: 2 CPU, 4GB RAM

---

## Infrastructure Setup

### 1. Cloud Provider Setup

#### AWS

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.1.0/24  # Public
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.2.0/24  # Private

# Create RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier taskassistant-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.7 \
  --master-username admin \
  --master-user-password <secure-password> \
  --allocated-storage 100

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id taskassistant-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1
```

#### Google Cloud Platform

```bash
# Create Cloud SQL PostgreSQL
gcloud sql instances create taskassistant-db \
  --database-version=POSTGRES_14 \
  --tier=db-n1-standard-2 \
  --region=us-central1

# Create MemoryStore Redis
gcloud redis instances create taskassistant-redis \
  --size=4 \
  --region=us-central1 \
  --tier=standard
```

#### Docker Compose (Development/Small Scale)

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: taskassistant
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://admin:${DB_PASSWORD}@db:5432/taskassistant
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A app.core.celery_tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://admin:${DB_PASSWORD}@db:5432/taskassistant
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: celery -A app.core.celery_tasks beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://admin:${DB_PASSWORD}@db:5432/taskassistant
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

## Database Setup

### 1. Initialize Database

```bash
# Connect to PostgreSQL
psql -h <db-host> -U admin -d taskassistant

# Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# Exit psql
\q
```

### 2. Run Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://admin:<password>@<db-host>:5432/taskassistant"

# Run Alembic migrations
alembic upgrade head
```

### 3. Seed Initial Data (Optional)

```bash
# Run seed script
python seed_database.py
```

---

## Application Deployment

### 1. Environment Configuration

Create `.env.production`:

```bash
# Application
APP_NAME="Task Assistant AI"
DEBUG=False
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://admin:<password>@<db-host>:5432/taskassistant

# Redis
REDIS_URL=redis://<redis-host>:6379/0
CELERY_BROKER_URL=redis://<redis-host>:6379/1
CELERY_RESULT_BACKEND=redis://<redis-host>:6379/2

# Security
SECRET_KEY=<generate-secure-random-key>
ENCRYPTION_KEY=<generate-fernet-key>
ALLOWED_ORIGINS=https://app.yourdomain.com,https://yourdomain.com

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...

# Monitoring
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# CORS
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

### 2. Build Application

```bash
# Build Docker image
docker build -t taskassistant-api:latest .

# Or build for specific platform
docker build --platform linux/amd64 -t taskassistant-api:latest .
```

### 3. Deploy with Docker

```bash
# Run API server
docker run -d \
  --name taskassistant-api \
  --env-file .env.production \
  -p 8000:8000 \
  taskassistant-api:latest

# Run Celery worker
docker run -d \
  --name taskassistant-worker \
  --env-file .env.production \
  taskassistant-api:latest \
  celery -A app.core.celery_tasks worker --loglevel=info

# Run Celery beat
docker run -d \
  --name taskassistant-beat \
  --env-file .env.production \
  taskassistant-api:latest \
  celery -A app.core.celery_tasks beat --loglevel=info
```

### 4. Deploy with Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taskassistant-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: taskassistant-api
  template:
    metadata:
      labels:
        app: taskassistant-api
    spec:
      containers:
        - name: api
          image: taskassistant-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: taskassistant-secrets
                  key: database-url
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: taskassistant-secrets
                  key: secret-key
          resources:
            requests:
              memory: "4Gi"
              cpu: "2"
            limits:
              memory: "8Gi"
              cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: taskassistant-api
spec:
  selector:
    app: taskassistant-api
  ports:
    - port: 80
      targetPort: 8000
  type: LoadBalancer
```

Apply configuration:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f secrets.yaml
kubectl apply -f worker-deployment.yaml
```

### 5. Configure Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/taskassistant
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/taskassistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

---

## Monitoring & Logging

### 1. Sentry Configuration

Already integrated in code. Verify by checking logs:

```bash
# Check Sentry is initialized
docker logs taskassistant-api | grep -i sentry
```

### 2. Application Logging

Configure logging level:

```python
# In .env.production
LOG_LEVEL=INFO
```

View logs:

```bash
# Docker
docker logs -f taskassistant-api

# Kubernetes
kubectl logs -f deployment/taskassistant-api

# System logs
sudo journalctl -u taskassistant-api -f
```

### 3. Metrics (Prometheus)

Add Prometheus metrics endpoint:

```bash
# Install prometheus-fastapi-instrumentator
pip install prometheus-fastapi-instrumentator

# Metrics available at /metrics
curl http://localhost:8000/metrics
```

### 4. Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# Redis health
curl http://localhost:8000/health/redis

# Celery health
curl http://localhost:8000/health/celery
```

---

## Security Hardening

### 1. Firewall Rules

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. Database Security

```sql
-- Create read-only user for analytics
CREATE USER analytics_readonly WITH PASSWORD '<password>';
GRANT CONNECT ON DATABASE taskassistant TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Restrict public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

### 3. API Keys Rotation

```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate new Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Regular Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Scan for vulnerabilities
pip install safety
safety check

# Docker image scanning
docker scan taskassistant-api:latest
```

---

## Scaling

### 1. Horizontal Scaling

**API Servers**:

```bash
# Add more API server instances
docker service scale taskassistant-api=5

# Or with Kubernetes
kubectl scale deployment taskassistant-api --replicas=5
```

**Worker Servers**:

```bash
# Scale worker pool
docker service scale taskassistant-worker=10

# Or with Kubernetes
kubectl scale deployment taskassistant-worker --replicas=10
```

### 2. Database Scaling

**Read Replicas**:

```sql
-- Configure streaming replication
-- On primary
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD '<password>';

-- Update pg_hba.conf
host replication replicator <replica-ip>/32 md5
```

**Connection Pooling** (PgBouncer):

```ini
# pgbouncer.ini
[databases]
taskassistant = host=localhost port=5432 dbname=taskassistant

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### 3. Redis Scaling

**Redis Cluster**:

```bash
# Create 6-node cluster (3 masters, 3 replicas)
redis-cli --cluster create \
  redis1:6379 redis2:6379 redis3:6379 \
  redis4:6379 redis5:6379 redis6:6379 \
  --cluster-replicas 1
```

### 4. Load Balancing

**HAProxy Configuration**:

```cfg
# haproxy.cfg
frontend api_frontend
    bind *:80
    mode http
    default_backend api_backend

backend api_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    server api1 10.0.1.10:8000 check
    server api2 10.0.1.11:8000 check
    server api3 10.0.1.12:8000 check
```

---

## Maintenance

### 1. Backup Strategy

**Database Backups**:

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h <db-host> -U admin taskassistant | gzip > backup_$DATE.sql.gz

# Upload to S3
aws s3 cp backup_$DATE.sql.gz s3://taskassistant-backups/

# Cleanup old backups (keep 30 days)
find /backups -name "backup_*.sql.gz" -mtime +30 -delete
```

Schedule with cron:

```bash
0 2 * * * /opt/scripts/backup.sh
```

**Redis Backups**:

```bash
# Enable RDB snapshots
redis-cli CONFIG SET save "900 1 300 10 60 10000"

# Manual backup
redis-cli BGSAVE
```

### 2. Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE taskassistant;

-- Check bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Log Rotation

```bash
# /etc/logrotate.d/taskassistant
/var/log/taskassistant/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload taskassistant-api
    endscript
}
```

### 4. Monitoring Checklist

- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] Disk usage < 80%
- [ ] Database connections < max_connections \* 0.8
- [ ] Response time < 500ms (p95)
- [ ] Error rate < 0.1%
- [ ] Celery queue length < 1000

### 5. Zero-Downtime Deployment

```bash
# Blue-green deployment script
#!/bin/bash

# Deploy new version (green)
docker build -t taskassistant-api:green .
docker run -d --name api-green taskassistant-api:green

# Health check
while ! curl -f http://localhost:8001/health; do
    sleep 5
done

# Switch traffic (update load balancer)
# HAProxy runtime API or update Kubernetes service

# Stop old version (blue)
docker stop api-blue
docker rm api-blue

# Tag new version as blue for next deployment
docker tag taskassistant-api:green taskassistant-api:blue
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Pool Exhausted**

```bash
# Increase pool size in config
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=10
```

**2. Redis Memory Full**

```bash
# Set maxmemory policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 4gb
```

**3. Celery Workers Dying**

```bash
# Increase worker memory limit
celery -A app.core.celery_tasks worker --max-memory-per-child=500000

# Check for memory leaks
celery -A app.core.celery_tasks inspect stats
```

**4. High API Latency**

```bash
# Enable query logging
ALTER DATABASE taskassistant SET log_statement = 'all';
ALTER DATABASE taskassistant SET log_duration = on;

# Analyze slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database created and migrations run
- [ ] Redis accessible
- [ ] SSL certificates obtained
- [ ] API keys configured
- [ ] Sentry project created

### Deployment

- [ ] Application deployed
- [ ] Workers running
- [ ] Beat scheduler running
- [ ] Reverse proxy configured
- [ ] Health checks passing

### Post-Deployment

- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team notified

---

## Support

For deployment issues:

- **Email**: devops@taskassistant.ai
- **Slack**: #deployments
- **Docs**: https://docs.taskassistant.ai/deployment
