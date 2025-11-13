# Security Policy

## Reporting Security Vulnerabilities

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- **Email**: security@vastai-research.org (if available)
- **Private Security Advisory**: Use GitHub's private vulnerability reporting feature

We take security seriously and will respond within 48 hours.

## Security Measures Implemented

### 1. Authentication & Session Management

**Session Security:**
- HTTPOnly cookies to prevent XSS attacks
- Secure flag enabled for HTTPS environments
- Session expiration after 24 hours of inactivity
- Automatic session cleanup for expired sessions

**Implementation:**
```python
# Secure session cookie configuration
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,      # Prevents JavaScript access
    secure=True,        # HTTPS only
    samesite="strict",  # CSRF protection
    max_age=86400       # 24 hours
)
```

### 2. CSRF Protection

**Cross-Site Request Forgery (CSRF) Protection:**
- CSRF tokens required for all state-changing operations (POST, PUT, DELETE)
- Tokens stored in HTTPOnly cookies
- Validation via `X-CSRF-Token` header
- Token rotation on each request

**Usage:**
```javascript
// Get CSRF token
const response = await fetch('/api/csrf-token');
const { csrf_token } = await response.json();

// Include in subsequent requests
await fetch('/api/upload', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrf_token
  },
  body: formData
});
```

### 3. Input Validation

**File Upload Validation:**
- Extension whitelist (`.obj`, `.fbx`, `.glb`, `.vrm` only)
- MIME type verification using python-magic
- File size limit (100MB default)
- Malicious content scanning
- Path traversal prevention

**Implementation:**
```python
ALLOWED_EXTENSIONS = {".obj", ".fbx", ".glb", ".vrm"}
ALLOWED_MIME_TYPES = {
    "model/obj",
    "model/gltf-binary",
    "application/octet-stream",
}

def validate_file(file: UploadFile) -> bool:
    # Extension check
    if not is_valid_extension(file.filename):
        raise InvalidFormatError()
    
    # MIME type check
    mime = magic.from_buffer(file.file.read(2048), mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise SecurityError("Invalid MIME type")
    
    # Size check
    if file.size > MAX_FILE_SIZE:
        raise FileSizeExceededError()
```

**Path Traversal Prevention:**
```python
def sanitize_filename(filename: str) -> str:
    """Prevent path traversal attacks."""
    # Remove null bytes
    if "\x00" in filename:
        raise SecurityError("Null byte in filename")
    
    # Check for directory traversal
    if ".." in filename or filename.startswith("/"):
        raise SecurityError("Path traversal attempt detected")
    
    # Sanitize to safe characters only
    return secure_filename(filename)
```

### 4. Rate Limiting

**Upload Rate Limits:**
- 10 uploads per hour per session
- In-memory tracking with Redis backend
- Sliding window algorithm

**Job Limits:**
- Maximum 1 concurrent job per session
- Prevents GPU memory exhaustion
- Queue-based processing for fairness

**Implementation:**
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    
    if request.method == "POST" and "/upload" in request.url.path:
        upload_count = get_upload_count(session_id, window=3600)
        if upload_count >= 10:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
```

### 5. Security Headers

**HTTP Security Headers:**
```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' ws: wss:"
)
```

### 6. Secure File Deletion

**Secure Deletion with Shred:**
- Uses `shred` utility on Linux for secure file deletion
- Overwrites file data multiple times
- Prevents data recovery from deleted files

**Implementation:**
```python
def secure_delete_file(file_path: Path) -> None:
    """Securely delete a file using shred."""
    try:
        subprocess.run(
            ["shred", "-uz", str(file_path)],
            check=True,
            capture_output=True
        )
    except FileNotFoundError:
        # Fallback to standard deletion
        file_path.unlink(missing_ok=True)
```

### 7. SQL Injection Prevention

**ORM Usage:**
- SQLAlchemy ORM prevents SQL injection
- Parameterized queries only
- No raw SQL execution with user input

**Example:**
```python
# Safe: Using ORM
job = session.query(Job).filter(Job.id == job_id).first()

# Unsafe (NEVER DO THIS):
# query = f"SELECT * FROM jobs WHERE id = '{job_id}'"
# session.execute(query)
```

### 8. Dependency Security

**Dependency Management:**
- Regular updates for security patches
- Pinned versions in `requirements.txt`
- Automated dependency scanning (Dependabot)
- Known vulnerability checks

**Verify Dependencies:**
```bash
# Check for known vulnerabilities
pip install safety
safety check --json

# Update dependencies
pip list --outdated
pip install -U <package>
```

### 9. Docker Security

**Container Isolation:**
- Non-root user in containers
- Read-only root filesystem where possible
- Limited capabilities
- Network isolation

**Dockerfile Best Practices:**
```dockerfile
# Use specific versions
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Run with limited permissions
RUN chmod 600 /app/config.yaml
```

**Volume Permissions:**
```bash
# Set restrictive permissions on host
chmod 700 uploads/ results/
chown -R $(id -u):$(id -g) uploads/ results/
```

### 10. GPU Security

**GPU Isolation:**
- Worker containers have exclusive GPU access
- Resource limits prevent GPU memory exhaustion
- Automatic cleanup on job failure

## Security Checklist for Developers

When contributing, ensure:

- [ ] No hardcoded credentials or API keys
- [ ] Input validation on all user input
- [ ] Parameterized database queries only
- [ ] CSRF token validation on state-changing operations
- [ ] File uploads are validated (extension, MIME, size)
- [ ] Sensitive data is not logged
- [ ] Error messages don't expose internal details
- [ ] Dependencies are up to date
- [ ] Code reviewed by security-aware developer
- [ ] Tests include security edge cases

## Security Best Practices for Deployment

### 1. Use HTTPS

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH only from trusted IPs
sudo ufw enable
```

### 3. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull
docker compose up -d

# Update application
git pull origin main
docker compose build --no-cache
docker compose up -d
```

### 4. Monitoring & Logging

**Enable Audit Logging:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/unirig/audit.log'),
        logging.StreamHandler()
    ]
)

# Log security events
logger.info(f"Upload attempt from session {session_id}: {filename}")
logger.warning(f"Rate limit exceeded for session {session_id}")
logger.error(f"Invalid file upload attempt: {filename}")
```

**Monitor Failed Attempts:**
```bash
# Watch for suspicious activity
tail -f /var/log/unirig/audit.log | grep -i "failed\|error\|denied"

# Count failed login attempts (if implemented)
grep "authentication failed" /var/log/unirig/audit.log | wc -l
```

### 5. Backup & Recovery

**Secure Backups:**
```bash
# Encrypt backups
tar czf - uploads/ | gpg --symmetric --cipher-algo AES256 -o uploads_backup.tar.gz.gpg

# Decrypt
gpg --decrypt uploads_backup.tar.gz.gpg | tar xzf -
```

### 6. Network Segmentation

**Docker Network Isolation:**
```yaml
# docker-compose.yml
services:
  backend:
    networks:
      - frontend-network
      - backend-network
  
  worker:
    networks:
      - backend-network
  
  nginx:
    networks:
      - frontend-network

networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true  # No external access
```

## Known Security Limitations

1. **No User Authentication**: Current version uses session-based tracking without user accounts. For production deployment with multiple users, implement proper authentication (OAuth2, JWT, etc.)

2. **Local File Storage**: Files are stored on local filesystem. For production, consider:
   - Encrypted filesystem
   - Cloud storage (S3, GCS) with signed URLs
   - Regular cleanup policies

3. **GPU Access**: Worker containers have full GPU access. If running untrusted models, consider:
   - GPU virtualization (vGPU)
   - Separate GPU per tenant
   - Resource quotas

4. **WebSocket Security**: WebSocket connections don't currently have authentication. Consider adding token-based auth for WebSocket endpoints.

## Incident Response

If a security incident occurs:

1. **Isolate**: Stop affected services
```bash
docker compose stop backend worker
```

2. **Investigate**: Check logs for suspicious activity
```bash
docker compose logs backend | grep ERROR
docker compose logs worker | grep ERROR
```

3. **Remediate**: Apply fixes, update dependencies
4. **Notify**: Report to security team and affected users
5. **Document**: Record incident details for future prevention

## Security Contact

For security concerns:
- **Email**: security@vastai-research.org
- **GPG Key**: [Link to public key if available]
- **Response Time**: 48 hours for initial response

## Acknowledgments

We thank the security community for responsible disclosure of vulnerabilities.

---

**Last Updated**: November 13, 2025  
**Version**: 1.0
