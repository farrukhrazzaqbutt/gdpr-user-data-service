# GDPR-aware User Data Service

A privacy-by-design user data service demonstrating GDPR compliance with PII encryption, consent tracking, and Right-to-be-Forgotten (RTBF) capabilities.

## Features

- **PII Encryption at Rest**: Uses envelope encryption with random data keys encrypted by a master key
- **Consent Management**: Track and manage user consents for different data processing purposes
- **Right-to-be-Forgotten**: Automated anonymization of user data upon request
- **Audit Logging**: Comprehensive, append-only audit trail for all data operations
- **GDPR Compliance**: Built-in tools for data export and deletion requests

## Architecture

### Models

- **User**: Stores encrypted PII data and basic user information
- **Consent**: Tracks user consent for different processing purposes
- **AuditLog**: Immutable audit trail of all operations
- **DeletionRequest**: Manages RTBF requests and their processing status

### Security

- **Envelope Encryption**: PII data encrypted with random data keys, which are encrypted with a master key
- **AES-GCM Encryption**: Industry-standard encryption for data keys
- **PBKDF2 Key Derivation**: Secure key derivation from master key
- **JWT Authentication**: Secure API access with role-based permissions

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd user_data_service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.sample .env
   # Edit .env with your database and encryption settings
   ```

3. **Setup database**:
   ```bash
   # Start PostgreSQL and Redis
   # Update DATABASE_URL in .env
   python -c "from app.db import engine, Base; Base.metadata.create_all(bind=engine)"
   ```

4. **Run the service**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Development

1. **Start services**:
   ```bash
   docker-compose up -d
   ```

2. **Access the service**:
   - API: http://localhost:8000
   - Database: localhost:5432
   - Redis: localhost:6379

## API Usage

### Authentication

1. **Seed admin user** (development only):
   ```bash
   curl -X POST http://localhost:8000/auth/seed
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin"
   ```

### User Management

1. **Create user with PII**:
   ```bash
   curl -X POST http://localhost:8000/users/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "pii_data": {
         "name": "John Doe",
         "phone": "+1234567890",
         "address": "123 Main St"
       },
       "consent_purposes": ["marketing", "analytics"]
     }'
   ```

2. **Get user (without PII)**:
   ```bash
   curl -X GET http://localhost:8000/users/1 \
     -H "Authorization: Bearer <token>"
   ```

3. **Get user with PII**:
   ```bash
   curl -X GET http://localhost:8000/users/1/with-pii \
     -H "Authorization: Bearer <token>"
   ```

4. **Export user data**:
   ```bash
   curl -X GET http://localhost:8000/users/1/export \
     -H "Authorization: Bearer <token>"
   ```

### Consent Management

1. **Create consent**:
   ```bash
   curl -X POST http://localhost:8000/consents/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "purpose": "marketing",
       "granted": true
     }'
   ```

2. **Get user consents**:
   ```bash
   curl -X GET "http://localhost:8000/consents/?user_id=1" \
     -H "Authorization: Bearer <token>"
   ```

### Right-to-be-Forgotten

1. **Create deletion request**:
   ```bash
   curl -X POST http://localhost:8000/rtbf/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}'
   ```

2. **Process deletion request** (admin only):
   ```bash
   curl -X POST http://localhost:8000/rtbf/1/process \
     -H "Authorization: Bearer <admin_token>"
   ```

### Audit Logs

1. **Get audit logs** (admin only):
   ```bash
   curl -X GET "http://localhost:8000/audit/?user_id=1" \
     -H "Authorization: Bearer <admin_token>"
   ```

## Background Processing

The service includes a Celery worker for processing RTBF requests:

```bash
# Start the worker
celery -A app.workers.celery_app worker -Q default -l info

# Or use Docker Compose (includes worker)
docker-compose up
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_crypto.py
```

### Test Coverage

- **Crypto Tests**: Encryption/decryption round-trip, tamper detection
- **Model Tests**: Database model creation and relationships
- **API Tests**: All endpoint functionality
- **Integration Tests**: End-to-end workflows

## Security Considerations

### Production Deployment

1. **Change default secrets**:
   - Update `SECRET_KEY` in environment
   - Generate a strong `MASTER_KEY` (32 bytes)
   - Use proper key management (AWS KMS, Azure Key Vault, etc.)

2. **Database security**:
   - Use encrypted connections (SSL/TLS)
   - Implement proper access controls
   - Regular security updates

3. **Network security**:
   - Use HTTPS in production
   - Implement rate limiting
   - Configure CORS appropriately

4. **Key rotation**:
   - Implement master key rotation procedure
   - Consider per-tenant encryption keys
   - Regular security audits

## GDPR Compliance Features

### Data Protection

- **Encryption at Rest**: All PII encrypted using envelope encryption
- **Access Controls**: Role-based access to PII data
- **Audit Trail**: Complete log of all data operations

### User Rights

- **Data Portability**: Export complete user data via `/users/{id}/export`
- **Right to Erasure**: RTBF processing with data anonymization
- **Consent Management**: Granular consent tracking and revocation

### Legal Compliance

- **Data Minimization**: Only collect necessary data
- **Purpose Limitation**: Process data only for specified purposes
- **Retention Limits**: Configurable data retention policies

## Data Map

| Data Type | Location | Purpose | Legal Basis | Retention |
|-----------|----------|---------|-------------|-----------|
| Email | `users.email` | Authentication | Legitimate Interest | Account lifetime |
| PII (name, phone, address) | `users.pii_encrypted` | Service delivery | Consent | Account lifetime |
| Consent records | `consents` | Compliance | Legal obligation | 7 years |
| Audit logs | `audit_logs` | Security & compliance | Legal obligation | 7 years |
| Deletion requests | `deletion_requests` | RTBF processing | Legal obligation | 7 years |

## Monitoring and Observability

- **Health Checks**: `/health` endpoint for service monitoring
- **Audit Logs**: Comprehensive operation logging
- **Error Tracking**: Structured error logging with context
- **Metrics**: Request/response timing and success rates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is a demonstration project for portfolio purposes. For production use, ensure:

- Proper security review and penetration testing
- Compliance with applicable data protection regulations
- Regular security updates and monitoring
- Professional legal and compliance review
