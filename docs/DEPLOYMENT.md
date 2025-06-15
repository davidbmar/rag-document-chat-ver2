# RAG System Deployment Guide

This guide covers deploying the RAG Document Chat System in various environments.

## Quick Start Deployment

### Local Development

```bash
# 1. Clone and setup
git clone <repo-url>
cd rag-document-chat
./setup.sh

# 2. Configure
cp .env.example .env
nano .env  # Add your API keys

# 3. Start services
source rag_env/bin/activate
source .env
docker-compose up -d
streamlit run app.py
```

## Production Deployment

### AWS EC2 Deployment

#### Instance Requirements
- **Instance Type**: t3.medium or larger (2 vCPU, 4GB RAM minimum)
- **Storage**: 20GB+ SSD
- **Security Group**: Ports 22, 8501, 8002, 8001
- **IAM Role**: S3 access if using S3 storage

#### Step-by-Step EC2 Setup

1. **Launch EC2 Instance**
   ```bash
   # Connect to your instance
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Prerequisites**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   
   # Install Python and tools
   sudo apt install -y python3-pip python3-venv git nginx
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd rag-document-chat
   
   # Run setup
   chmod +x setup.sh
   ./setup.sh
   
   # Configure environment
   cp .env.example .env
   nano .env  # Add production credentials
   ```

4. **Configure Nginx (Optional)**
   ```nginx
   # /etc/nginx/sites-available/rag-system
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /api {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Create Systemd Services**
   
   **Streamlit Service** (`/etc/systemd/system/rag-streamlit.service`):
   ```ini
   [Unit]
   Description=RAG Streamlit Application
   After=network.target docker.service
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/rag-document-chat
   Environment=PATH=/home/ubuntu/rag-document-chat/rag_env/bin
   EnvironmentFile=/home/ubuntu/rag-document-chat/.env
   ExecStart=/home/ubuntu/rag-document-chat/rag_env/bin/streamlit run app.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   **API Service** (`/etc/systemd/system/rag-api.service`):
   ```ini
   [Unit]
   Description=RAG FastAPI Application
   After=network.target docker.service
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/rag-document-chat
   Environment=PATH=/home/ubuntu/rag-document-chat/rag_env/bin
   EnvironmentFile=/home/ubuntu/rag-document-chat/.env
   ExecStart=/home/ubuntu/rag-document-chat/rag_env/bin/python app.py api
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Services**
   ```bash
   sudo systemctl enable rag-streamlit rag-api
   sudo systemctl start rag-streamlit rag-api
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

### Google Cloud Platform

#### Compute Engine Setup

1. **Create VM Instance**
   ```bash
   gcloud compute instances create rag-system \
     --zone=us-central1-a \
     --machine-type=e2-medium \
     --boot-disk-size=20GB \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --tags=http-server,https-server
   ```

2. **Configure Firewall**
   ```bash
   gcloud compute firewall-rules create allow-rag-ports \
     --allow tcp:8501,tcp:8001,tcp:8002 \
     --source-ranges 0.0.0.0/0 \
     --description "Allow RAG system ports"
   ```

3. **Deploy Application**
   ```bash
   # SSH to instance
   gcloud compute ssh rag-system --zone=us-central1-a
   
   # Follow same deployment steps as EC2
   ```

### Docker Production Deployment

#### Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: rag_chromadb
    ports:
      - "8002:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - ANONYMIZED_TELEMETRY=False
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  rag-app:
    build: .
    container_name: rag_app
    ports:
      - "8501:8501"
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
    depends_on:
      - chromadb
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  nginx:
    image: nginx:alpine
    container_name: rag_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - rag-app
    restart: unless-stopped

volumes:
  chromadb_data:
```

#### Production Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY .env .

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8501 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501 || exit 1

# Start application
CMD ["python", "app.py"]
```

## Environment-Specific Configurations

### Production Environment Variables

```bash
# Production .env
OPENAI_API_KEY=sk-prod-key-here
AWS_ACCESS_KEY_ID=prod-access-key
AWS_SECRET_ACCESS_KEY=prod-secret-key
S3_BUCKET=prod-rag-documents
CHROMA_HOST=chromadb
CHROMA_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Development Environment

```bash
# Development .env
OPENAI_API_KEY=sk-dev-key-here
AWS_ACCESS_KEY_ID=dev-access-key
AWS_SECRET_ACCESS_KEY=dev-secret-key
S3_BUCKET=dev-rag-documents
CHROMA_HOST=localhost
CHROMA_PORT=8002
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

## SSL/HTTPS Setup

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom SSL Certificate

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8501;
        # ... other proxy settings
    }
}
```

## Monitoring and Logging

### Application Monitoring

1. **Health Checks**
   ```bash
   # Create monitoring script
   cat > monitor.sh << 'EOF'
   #!/bin/bash
   # Check services
   curl -f http://localhost:8501/ || echo "Streamlit down"
   curl -f http://localhost:8001/ || echo "API down"
   curl -f http://localhost:8002/api/v1/heartbeat || echo "ChromaDB down"
   EOF
   ```

2. **Log Aggregation**
   ```bash
   # Centralized logging
   sudo apt install rsyslog
   # Configure to send logs to central server
   ```

### Performance Monitoring

```python
# Add to app.py for metrics
import time
import psutil

def get_system_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
```

## Backup and Recovery

### Database Backup

```bash
# Backup ChromaDB data
docker-compose exec chromadb tar -czf /tmp/chroma_backup.tar.gz /chroma/chroma
docker cp chromadb:/tmp/chroma_backup.tar.gz ./backups/

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec chromadb tar -czf /tmp/chroma_backup_$DATE.tar.gz /chroma/chroma
docker cp chromadb:/tmp/chroma_backup_$DATE.tar.gz ./backups/
# Upload to S3 or other backup storage
EOF
```

### Application Recovery

```bash
# Recovery script
cat > recover.sh << 'EOF'
#!/bin/bash
# Stop services
docker-compose down

# Restore backup
docker-compose up -d chromadb
sleep 10
docker cp ./backups/chroma_backup.tar.gz chromadb:/tmp/
docker-compose exec chromadb tar -xzf /tmp/chroma_backup.tar.gz -C /

# Restart services
docker-compose restart
EOF
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup**
   - Use nginx or cloud load balancer
   - Multiple app instances
   - Shared ChromaDB instance

2. **Database Scaling**
   - ChromaDB clustering (enterprise)
   - External vector database (Pinecone, Weaviate)

### Vertical Scaling

1. **Resource Optimization**
   - Increase CPU/memory for embeddings
   - SSD storage for faster I/O
   - GPU instances for local embeddings

## Security Best Practices

### Application Security

1. **API Key Management**
   ```bash
   # Use AWS Secrets Manager
   pip install boto3
   # Retrieve secrets in application
   ```

2. **Network Security**
   ```bash
   # Firewall rules
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

3. **Authentication**
   ```python
   # Add authentication to Streamlit
   import streamlit_authenticator as stauth
   ```

### Data Security

1. **Encryption at Rest**
   - Encrypt disk volumes
   - Use encrypted S3 buckets

2. **Encryption in Transit**
   - HTTPS/SSL for all connections
   - VPN for internal communication

## Troubleshooting Common Issues

### Service Not Starting

```bash
# Check service status
sudo systemctl status rag-streamlit
sudo systemctl status rag-api

# Check Docker containers
docker-compose ps
docker-compose logs chromadb

# Check ports
sudo netstat -tlnp | grep :8501
sudo netstat -tlnp | grep :8001
sudo netstat -tlnp | grep :8002
```

### Performance Issues

```bash
# Monitor resources
htop
df -h
free -m

# Check application logs
tail -f logs/app.log
docker-compose logs -f rag-app
```

### Network Issues

```bash
# Test connectivity
curl -v http://localhost:8501
curl -v http://localhost:8001
curl -v http://localhost:8002/api/v1/heartbeat

# Check firewall
sudo ufw status
sudo iptables -L
```

## Cost Optimization

### AWS Cost Management

1. **Instance Sizing**
   - Start with t3.medium
   - Monitor and adjust based on usage
   - Use spot instances for development

2. **Storage Optimization**
   - Use gp3 volumes instead of gp2
   - Implement S3 lifecycle policies
   - Regular cleanup of old documents

3. **Monitoring Costs**
   ```bash
   # Set up billing alerts
   # Use AWS Cost Explorer
   # Implement auto-shutdown for dev environments
   ```

## Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade
   
   # Backup databases
   ./backup.sh
   
   # Check logs for errors
   grep ERROR /var/log/syslog
   ```

2. **Monthly**
   ```bash
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   
   # Clean up unused Docker resources
   docker system prune -f
   
   # Review and rotate logs
   sudo logrotate -f /etc/logrotate.conf
   ```

3. **Quarterly**
   - Review and update Python dependencies
   - Security audit and vulnerability scanning
   - Performance testing and optimization
   - Disaster recovery testing

### Automated Maintenance

Create maintenance scripts:

```bash
# /opt/rag-maintenance/daily.sh
#!/bin/bash
LOG_FILE="/var/log/rag-maintenance.log"

echo "$(date): Starting daily maintenance" >> $LOG_FILE

# Check service health
systemctl is-active --quiet rag-streamlit || systemctl restart rag-streamlit
systemctl is-active --quiet rag-api || systemctl restart rag-api

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): WARNING: Disk usage is $DISK_USAGE%" >> $LOG_FILE
fi

# Backup ChromaDB
/opt/rag-maintenance/backup.sh

echo "$(date): Daily maintenance completed" >> $LOG_FILE
```

## Integration with CI/CD

### GitHub Actions Deployment

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy RAG System

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /home/ubuntu/rag-document-chat
          git pull origin main
          source rag_env/bin/activate
          pip install -r requirements.txt
          docker-compose restart chromadb
          sudo systemctl restart rag-streamlit rag-api
```

### Automated Testing

```yaml
name: Test RAG System

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Start ChromaDB
      run: |
        docker run -d --name chromadb -p 8002:8000 chromadb/chroma
        sleep 10
    
    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python test_setup.py
        pytest tests/ -v
```

This completes the comprehensive deployment guide covering everything from local development to production scaling and maintenance.
