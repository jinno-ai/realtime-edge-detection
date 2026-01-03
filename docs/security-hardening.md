# Security Hardening Guide

Guide for deploying the edge detection system securely in production environments.

## Table of Contents

- [Model Security](#model-security)
- [Dependency Security](#dependency-security)
- [Configuration Security](#configuration-security)
- [API Security](#api-security)
- [Deployment Security](#deployment-security)
- [Edge Device Security](#edge-device-security)

---

## Model Security

### Model Verification

Always verify model file integrity before use:

```python
from src.models.verification import verify_model_before_load

# Verify model before loading
if verify_model_before_load('yolov8n.pt', strict=True):
    detector = YOLODetector(model_path='yolov8n.pt')
else:
    raise ValueError("Model verification failed")
```

### Model File Integrity

**Checksums:**
- Store SHA256 checksums of all models
- Verify checksums after download
- Checksum file: `models/checksums.json`

```json
{
  "models": {
    "yolov8n.pt": {
      "sha256": "abc123...",
      "size": 6000000,
      "path": "models/yolov8n.pt"
    }
  }
}
```

**Download from Trusted Sources:**
- Only download models from official repositories
- Verify HTTPS certificates
- Check digital signatures if available

### Model Sandboxing

**Load Models in Isolated Environment:**

```python
from src.models.verification import sandbox_model_load

# Check if model is safe to load
if sandbox_model_load('untrusted_model.onnx'):
    detector = ONNXDetector(model_path='untrusted_model.onnx')
else:
    raise ValueError("Unsafe model")
```

**Restrict Model Operations:**
- Validate ONNX models before loading
- Check model structure and operations
- Block models with suspicious operations

---

## Dependency Security

### Regular Vulnerability Scanning

**Automated Scanning:**

```bash
# Run security audit
python scripts/security_audit.py

# Or run individual tools
pip-audit
safety check
bandit -r src/
```

**CI/CD Integration:**

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/
```

### Dependency Updates

**Keep Dependencies Updated:**
```bash
# Check for updates
pip list --outdated

# Update requirements
pip-compile requirements.in --upgrade

# Run security scan after updates
python scripts/security_audit.py
```

**Pin Dependency Versions:**
```
# requirements.txt - Pin exact versions
opencv-python==4.8.1.78
torch==2.0.1
numpy==1.24.3
```

### Vulnerability Response

**If Vulnerabilities Are Found:**

1. **Assess Severity:**
   - Critical: Fix immediately
   - High: Fix within 24 hours
   - Medium: Fix within 1 week
   - Low: Fix in next update

2. **Update Package:**
   ```bash
   pip install --upgrade <package_name>
   ```

3. **Verify Fix:**
   ```bash
   pip-audit  # Confirm vulnerability is resolved
   ```

4. **Test Thoroughly:**
   - Run full test suite
   - Check for breaking changes

---

## Configuration Security

### Secret Management

**Never Hardcode Secrets:**

```python
# BAD - Hardcoded secret
API_KEY = "sk-1234567890abcdef"

# GOOD - Environment variable
import os
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not set")
```

**Use Environment Variables:**
```bash
# .env file (add to .gitignore!)
API_KEY=sk-1234567890abcdef
DATABASE_URL=postgresql://user:pass@localhost/db

# Load in Python
from dotenv import load_dotenv
load_dotenv()
```

**Secret Masking in Logs:**

```python
from src.security.secret_masking import get_safe_config

# Mask sensitive config before logging
config = {
    'model_path': 'yolov8n.pt',
    'api_key': 'sk-1234567890abcdef'
}

safe_config = get_safe_config(config)
logger.info(f"Config: {safe_config}")
# Output: Config: {'model_path': 'yolov8n.pt', 'api_key': '******cdef'}
```

### Configuration Validation

**Validate Configuration:**

```python
from src.config.config_manager import ConfigManager
from src.core.errors import ValidationError

try:
    config = ConfigManager('config.yaml')
    if not config.validate():
        raise ValidationError("Invalid configuration")
except ValidationError as e:
    logger.error(f"Config validation failed: {e}")
    sys.exit(1)
```

**File Permissions:**
```bash
# Restrict config file permissions
chmod 600 config.yaml  # Owner read/write only

# Verify
ls -la config.yaml
# Should show: -rw------- (600)
```

---

## API Security

### CORS Configuration

**If running API server:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-domain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specific methods
    allow_headers=["Content-Type"],  # Specific headers
)
```

### Security Headers

**Enable Security Headers:**

```python
from fastapi import Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Only allow trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.trusted-domain.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Rate Limiting

**Prevent Abuse:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/detect")
@limiter.limit("10/minute")  # 10 requests per minute
async def detect(request: Request):
    ...
```

### Input Validation

**Validate All Inputs:**

```python
from pydantic import BaseModel, validator

class DetectionRequest(BaseModel):
    image_url: str
    confidence: float = 0.5

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0 and 1')
        return v

    @validator('image_url')
    def validate_url(cls, v):
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Invalid URL')
        return v
```

---

## Deployment Security

### Docker Security

**Use Minimal Base Image:**

```dockerfile
# Good - Minimal image
FROM python:3.11-slim

# Bad - Large image with extra tools
FROM python:3.11
```

**Run as Non-Root User:**

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Run application
CMD ["python", "-m", "src.cli.main"]
```

**Scan Docker Images:**

```bash
# Scan for vulnerabilities
docker scan edge-detection:latest

# Use Trivy for more detailed scan
trivy image edge-detection:latest
```

### Kubernetes Security

**Use Security Contexts:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: edge-detection
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: edge-detection:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

**Network Policies:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: edge-detection-netpol
spec:
  podSelector:
    matchLabels:
      app: edge-detection
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### Environment Isolation

**Use Separate Environments:**
- Development
- Staging
- Production

**Environment Variables:**
```bash
# Production environment
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export API_KEY=<production-key>

# Development environment
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export API_KEY=<dev-key>
```

---

## Edge Device Security

### Device Hardening

**1. Secure Boot:**
- Enable secure boot if available
- Use signed firmware
- Verify bootloader integrity

**2. Minimal Installation:**
- Install only required packages
- Remove unnecessary services
- Disable unused ports

**3. User Management:**
```bash
# Create dedicated user for application
sudo useradd -m -s /bin/bash edgeapp

# Grant specific permissions
sudo usermod -aG video edgeapp  # For camera access
```

### Network Security

**Firewall Configuration:**
```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Application
sudo ufw enable
```

**VPN for Remote Access:**
- Use VPN for remote device management
- Never expose device directly to internet
- Use wireguard or OpenVPN

### Data Security

**Encrypt Sensitive Data:**
```python
from cryptography.fernet import Fernet

# Encrypt model files
key = Fernet.generate_key()
cipher = Fernet(key)

with open('model.pt', 'rb') as f:
    model_data = f.read()

encrypted = cipher.encrypt(model_data)

with open('model.pt.enc', 'wb') as f:
    f.write(encrypted)
```

**Secure Data Transmission:**
- Always use HTTPS/TLS
- Verify SSL certificates
- Use mTLS for service-to-service

### Updates and Maintenance

**Signed Updates:**
```bash
# Verify GPG signature
gpg --verify update.tar.gz.sig update.tar.gz

# Extract and install
tar xzf update.tar.gz
cd update && sudo ./install.sh
```

**Automated Security Scans:**
```bash
# Weekly security scan
0 3 * * 0 /path/to/security_audit.py

# Daily dependency check
0 2 * * * pip-audit
```

---

## Security Checklist

### Pre-Deployment

- [ ] All dependencies scanned for vulnerabilities
- [ ] No hardcoded secrets in code
- [ ] Configuration files have restricted permissions
- [ ] Models verified with checksums
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Input validation implemented
- [ ] Logging doesn't leak secrets

### Post-Deployment

- [ ] Run security audit weekly
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated
- [ ] Review access logs regularly
- [ ] Test incident response procedures
- [ ] Maintain security documentation

### Incident Response

**If Security Incident Occurs:**

1. **Identify Scope:**
   - What systems affected?
   - What data exposed?

2. **Contain:**
   - Isolate affected systems
   - Rotate compromised credentials
   - Block malicious IPs

3. **Eradicate:**
   - Patch vulnerabilities
   - Remove malware
   - Fix misconfigurations

4. **Recover:**
   - Restore from clean backups
   - Monitor for recurrence
   - Document lessons learned

---

## Resources

- **OWASP:** https://owasp.org/
- **CWE:** https://cwe.mitre.org/
- **CVE Database:** https://cve.mitre.org/
- **PyTorch Security:** https://github.com/pytorch/pytorch/blob/main/SECURITY.md
- **Docker Security:** https://docs.docker.com/engine/security/
