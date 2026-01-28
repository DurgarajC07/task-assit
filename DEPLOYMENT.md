# Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Production Checklist](#production-checklist)
5. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development

### Quick Start

```bash
# 1. Clone and setup
cd /home/anvex/workspace/multiagent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY

# 5. Start server
uvicorn app.main:app --reload

# Or use startup script
./start.sh --seed  # Unix/Mac
start.bat --seed   # Windows
```

### Access Points

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## Docker Deployment

### Build and Run

```bash
# 1. Build image
docker build -t task-assistant:latest .

# 2. Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key-here \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG=false \
  task-assistant:latest

# 3. Or use docker-compose
docker-compose up -d
```

### Docker Compose Setup

```yaml
# Production configuration
version: '3.8'

services:
  api:
    image: task-assistant:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=taskuser
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=task_assistant
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskuser"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Deployment with Compose

```bash
# 1. Create .env file
cp .env.example .env
# Edit with production values

# 2. Build custom image (optional)
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Run migrations (if using Alembic)
docker-compose exec api alembic upgrade head

# 5. Check logs
docker-compose logs -f api

# 6. Stop services
docker-compose down
```

## AWS Deployment

### Option 1: ECS (Elastic Container Service)

#### Prerequisites
- AWS account with ECS access
- Docker image in ECR (Elastic Container Registry)
- RDS PostgreSQL database

#### Step 1: Create ECR Repository

```bash
# 1. Create repository
aws ecr create-repository --repository-name task-assistant

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# 3. Tag image
docker tag task-assistant:latest [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/task-assistant:latest

# 4. Push image
docker push [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/task-assistant:latest
```

#### Step 2: Create RDS Database

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier task-assistant-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username dbadmin \
  --master-user-password [SECURE_PASSWORD] \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxx
```

#### Step 3: Create ECS Task Definition

```json
{
  "family": "task-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "task-assistant",
      "image": "[ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/task-assistant:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DEBUG",
          "value": "false"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:anthropic-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/task-assistant",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 4: Create ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster task-assistant-cluster \
  --service-name task-assistant-service \
  --task-definition task-assistant:1 \
  --desired-count 2 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=task-assistant,containerPort=8000 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxx,subnet-xxxx],securityGroups=[sg-xxxx],assignPublicIp=ENABLED}"
```

### Option 2: Elastic Beanstalk

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize
eb init -p python-3.11 task-assistant

# 3. Create environment
eb create prod-env \
  --instance-type t3.micro \
  --scale 2

# 4. Set environment variables
eb setenv \
  ANTHROPIC_API_KEY=your-key \
  SECRET_KEY=your-secret \
  DATABASE_URL=postgresql://...

# 5. Deploy
eb deploy

# 6. Open URL
eb open
```

### Option 3: Lambda + API Gateway

```bash
# 1. Install serverless framework
npm install -g serverless

# 2. Configure serverless
serverless config credentials --provider aws

# 3. Deploy
serverless deploy

# 4. Get endpoint
serverless info
```

## Production Checklist

### Pre-Deployment

- [ ] **Environment Variables**
  - [ ] Set strong `SECRET_KEY`
  - [ ] Configure `ANTHROPIC_API_KEY`
  - [ ] Set `DEBUG=false`
  - [ ] Configure `ALLOWED_ORIGINS` properly
  - [ ] Set up database credentials securely

- [ ] **Database**
  - [ ] Use PostgreSQL (not SQLite)
  - [ ] Configure connection pooling
  - [ ] Enable SSL for connections
  - [ ] Set up automated backups
  - [ ] Run migrations

- [ ] **Security**
  - [ ] Enable HTTPS/SSL
  - [ ] Configure CORS properly
  - [ ] Set up WAF (Web Application Firewall)
  - [ ] Enable rate limiting
  - [ ] Set up authentication headers

- [ ] **Monitoring**
  - [ ] Configure logging (CloudWatch, ELK, etc.)
  - [ ] Set up monitoring and alerts
  - [ ] Configure error tracking (Sentry)
  - [ ] Set up uptime monitoring

- [ ] **Performance**
  - [ ] Enable caching headers
  - [ ] Configure CDN if needed
  - [ ] Set up auto-scaling
  - [ ] Optimize database queries
  - [ ] Configure request timeouts

- [ ] **Testing**
  - [ ] Run full test suite
  - [ ] Load testing (100+ concurrent users)
  - [ ] Security testing
  - [ ] Database backup/restore testing

### Deployment Steps

```bash
# 1. Build and tag image
docker build -t task-assistant:v1.0.0 .

# 2. Push to registry
docker push registry.example.com/task-assistant:v1.0.0

# 3. Deploy to production
kubectl apply -f deployment.yaml  # Kubernetes
# or
docker pull && docker-compose up -d  # Docker Compose
# or
eb deploy  # Elastic Beanstalk

# 4. Verify deployment
curl https://api.example.com/api/health

# 5. Monitor logs
tail -f /var/log/app.log
```

### Post-Deployment

- [ ] Verify all services are running
- [ ] Check database connectivity
- [ ] Test API endpoints
- [ ] Verify authentication
- [ ] Check logging and monitoring
- [ ] Run smoke tests

## Monitoring & Maintenance

### Health Checks

```bash
# API health
curl https://api.example.com/api/health

# Database connectivity
curl https://api.example.com/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

### Logs

```bash
# Docker logs
docker-compose logs -f api

# Kubernetes logs
kubectl logs -f deployment/task-assistant

# CloudWatch logs
aws logs tail /ecs/task-assistant --follow
```

### Metrics to Monitor

- **Availability**: % uptime
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: 4xx, 5xx errors per minute
- **Database**: Connection count, query time
- **Memory**: Memory usage and limits
- **CPU**: CPU usage and throttling

### Scaling Configuration

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: task-assistant-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: task-assistant
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Backup Strategy

```bash
# Daily database backup
0 2 * * * pg_dump -h localhost -U user db > backup_$(date +\%Y\%m\%d).sql

# Store in S3
aws s3 cp backup_*.sql s3://task-assistant-backups/

# Retention policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket task-assistant-backups \
  --lifecycle-configuration file://lifecycle.json
```

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: < 1 hour
2. **RPO (Recovery Point Objective)**: < 15 minutes

```bash
# Restore from backup
psql -h localhost -U user db < backup_20250127.sql

# Verify data
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM users;
```

### Updates & Patches

```bash
# Blue-green deployment
# 1. Deploy new version to green environment
# 2. Test new version
# 3. Switch traffic from blue to green
# 4. Keep blue as rollback

# Using docker-compose
# 1. Build new image
docker build -t task-assistant:v1.1.0 .

# 2. Update docker-compose.yml
# Change 'image: task-assistant:latest' to task-assistant:v1.1.0

# 3. Deploy with zero downtime
docker-compose up -d --no-deps --build api
```

### Cost Optimization

- Use reserved instances (20-30% discount)
- Implement auto-scaling
- Optimize database instance size
- Use spot instances for non-critical workloads
- Monitor and alert on cost anomalies

## Troubleshooting

### Common Issues

**Issue**: High memory usage
```bash
# Check processes
docker stats
# or
kubectl top pods
```

**Issue**: Database connection errors
```bash
# Check connection string
echo $DATABASE_URL
# Test connection
psql -h host -U user -d db -c "SELECT 1"
```

**Issue**: Slow API responses
```bash
# Check database query performance
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'uuid';
# Add missing indexes if needed
CREATE INDEX idx_user_id ON tasks(user_id);
```

**Issue**: WebSocket connections dropping
```bash
# Increase WebSocket timeout
# nginx: proxy_read_timeout 3600s;
# Or configure connection pooling
```

---

For questions or issues, refer to:
- Architecture Guide: `ARCHITECTURE.md`
- API Testing: `API_TESTING.md`
- README: `README.md`
