# Financial Services API - Docker Deployment

This document explains how to build and run the Financial Services API using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier deployment)

## Environment Configuration

Create a `.env` file in the project root with your configuration:

```bash
# Solr Configuration
SOLR_BASE_URL=https://solr.roguedev.local/solr
SOLR_CORE=financialservices

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration (optional, defaults to 8678)
PORT=8678
```

## Building and Running

### Option 1: Using Docker Compose (Recommended)

1. **Build and start the service:**
   ```bash
   docker-compose up -d --build
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f finserv-api
   ```

3. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t finserv-api .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name finserv-api \
     -p 8678:8678 \
     -e SOLR_BASE_URL=https://solr.roguedev.local/solr \
     -e SOLR_CORE=financialservices \
     -e GEMINI_API_KEY=your_gemini_api_key_here \
     -e PORT=8678 \
     finserv-api
   ```

3. **View logs:**
   ```bash
   docker logs -f finserv-api
   ```

4. **Stop the container:**
   ```bash
   docker stop finserv-api
   docker rm finserv-api
   ```

## Accessing the API

Once running, the API will be available at:
- **Swagger UI:** http://localhost:8678/docs
- **ReDoc:** http://localhost:8678/redoc
- **OpenAPI JSON:** http://localhost:8678/openapi.json

To use a different port, set the `PORT` environment variable:
```bash
# Example: Run on port 9000
docker-compose up -d
# or
docker run -e PORT=9000 -p 9000:9000 finserv-api
```

## Health Check

The Docker Compose configuration includes a health check that verifies the API is responding correctly. You can check the health status with:

```bash
docker-compose ps
```

## Features Included

The Docker image includes:
- FastAPI application with all endpoints
- Tesseract OCR for text extraction from scanned PDFs
- PyMuPDF for PDF processing
- Google Gemini AI integration for document summarization
- Apache Solr integration for document storage and search

## API Endpoints

- `POST /upload-pdf/` - Upload and process PDF documents
- `GET /update-summary/{doc_id}` - Update summary for existing documents
- `POST /update-summary-with-file/{doc_id}` - Update summary with OCR from uploaded file
- `GET /document/{doc_id}` - Get document information

## Troubleshooting

### Container won't start
- Check that all required environment variables are set
- Verify your `.env` file is in the correct location
- Check logs: `docker-compose logs finserv-api`

### OCR not working
- The image includes Tesseract OCR by default
- If issues persist, check container logs for OCR-related errors

### Cannot connect to Solr
- Verify `SOLR_BASE_URL` and `SOLR_CORE` are correct
- Ensure your Solr instance is accessible from the Docker container
- Check network connectivity and firewall settings

## Production Deployment

For production deployment:

1. **Use environment-specific configuration files**
2. **Set up proper logging and monitoring**
3. **Configure SSL/TLS termination at load balancer level**
4. **Use Docker secrets for sensitive information**
5. **Set up proper backup and recovery procedures**

## Security Notes

- Never commit `.env` files with real credentials to version control
- Use Docker secrets or external secret management in production
- Ensure Solr and Gemini API endpoints use secure connections
- Regularly update base images and dependencies for security patches
