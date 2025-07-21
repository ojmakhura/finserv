# Financial Services Document Processing API

A comprehensive, AI-powered document processing system designed for financial institutions. This FastAPI-based service provides intelligent PDF document analysis, OCR text extraction, AI summarization, and enterprise-grade document storage with Apache Solr integration.

## 🚀 Features

### Document Processing
- **PDF Upload & Analysis** - Secure document upload with automatic processing
- **Duplicate Detection** - SHA256 content-based duplicate prevention
- **Multi-Stage Text Extraction** - PyMuPDF for digital PDFs, Tesseract OCR for scanned documents
- **Intelligent Fallback** - Automatic OCR when standard text extraction fails

### AI-Powered Analysis
- **Document Summarization** - Google Gemini 1.5-flash for intelligent document analysis
- **Custom Questions** - Configurable summarization prompts for specific insights
- **Financial Document Focus** - Optimized for financial services content

### Enterprise Storage
- **Apache Solr Integration** - Scalable document indexing and search
- **Metadata Management** - Comprehensive document metadata tracking
- **Full-Text Search** - Advanced search capabilities across document corpus

### Production Ready
- **Docker Containerization** - Complete containerized deployment
- **Environment Configuration** - Secure environment variable management
- **Health Monitoring** - Built-in health checks and monitoring
- **API Documentation** - Auto-generated Swagger UI and ReDoc

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-pdf/` | Upload and process new PDF documents |
| `GET` | `/update-summary/{doc_id}` | Generate/update AI summary for existing documents |
| `POST` | `/update-summary-with-file/{doc_id}` | Update summary using OCR from uploaded file |
| `GET` | `/document/{doc_id}` | Retrieve document information and metadata |

## 🛠 Technology Stack

- **Backend**: FastAPI with async support
- **AI/ML**: Google Gemini 1.5-flash for document analysis
- **OCR**: Tesseract with optimized configuration
- **PDF Processing**: PyMuPDF (fitz) for text extraction
- **Document Storage**: Apache Solr for indexing and search
- **Containerization**: Docker & Docker Compose
- **Documentation**: Auto-generated OpenAPI/Swagger

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Apache Solr instance
- Google Gemini API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd finservices
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file with your configuration:
```bash
# Solr Configuration
SOLR_BASE_URL=https://your-solr-server.com/solr
SOLR_CORE=your_core_name

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration (optional, defaults to 8678)
PORT=8678
```

### 3. Build and Run
```bash
# Using Docker Compose (recommended)
docker-compose up -d --build

# Or using Docker directly
docker build -t finserv-api .
docker run -d --name finserv-api -p 8678:8678 --env-file .env finserv-api
```

### 4. Access the API
- **Swagger UI**: http://localhost:8678/docs
- **ReDoc**: http://localhost:8678/redoc
- **API Base**: http://localhost:8678/

## 📖 Usage Examples

### Upload a PDF Document
```bash
curl -X POST "http://localhost:8678/upload-pdf/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Get Document Summary
```bash
curl -X GET "http://localhost:8678/update-summary/doc_id_here"
```

### Custom Summarization Question
```bash
curl -X GET "http://localhost:8678/update-summary/doc_id_here?summarizing_question=What%20are%20the%20key%20financial%20risks%3F"
```

### Retrieve Document Information
```bash
curl -X GET "http://localhost:8678/document/doc_id_here"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SOLR_BASE_URL` | Base URL of your Solr instance | ✅ | - |
| `SOLR_CORE` | Solr core name for document storage | ✅ | - |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ | - |
| `PORT` | Server port | ❌ | 8678 |

### Solr Requirements
Your Solr core should have the following fields configured:
- `attr_content` - For document text content
- `attr_stream_source_info` - For file metadata
- `file_uri` - For document location tracking

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Apache Solr   │    │  Google Gemini  │
│                 │    │                 │    │                 │
│ • File Upload   │◄──►│ • Text Storage  │    │ • AI Analysis   │
│ • OCR Processing│    │ • Search Index  │    │ • Summarization │
│ • API Endpoints │    │ • Metadata      │    │ • Custom Q&A    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Tesseract     │
                    │   OCR Engine    │
                    │                 │
                    │ • Text Extract  │
                    │ • Image Process │
                    └─────────────────┘
```

## 🔍 Document Processing Flow

1. **Upload**: PDF document uploaded via API
2. **Hash Check**: SHA256 hash calculated for duplicate detection
3. **Text Extraction**: PyMuPDF attempts text extraction
4. **OCR Fallback**: If text extraction fails, Tesseract OCR processes document
5. **Storage**: Document and metadata stored in Solr
6. **AI Analysis**: Google Gemini generates intelligent summary
7. **Response**: Document ID and processing status returned

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Build production image
docker build -t finserv-api:latest .

# Run with production settings
docker run -d \
  --name finserv-api-prod \
  -p 8678:8678 \
  --env-file .env.production \
  --restart unless-stopped \
  finserv-api:latest
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8678/docs
```

### API Testing
Use the interactive Swagger UI at `http://localhost:8678/docs` for comprehensive API testing.

## 📊 Monitoring

The application includes built-in health checks:
- Container health monitoring via Docker
- API endpoint availability checks
- Dependency service connectivity

## 🛡 Security

- **Environment Variables**: All sensitive configuration externalized
- **SSL Support**: Configurable SSL verification for external services
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error responses without sensitive information exposure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [API Documentation](http://localhost:8678/docs)
- Review the [Docker README](Docker-README.md) for deployment issues
- Open an issue for bug reports or feature requests

## 🗂 Project Structure

```
finservices/
├── finserv_api.py              # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container orchestration
├── .env.example               # Environment configuration template
├── .dockerignore              # Docker build exclusions
├── README.md                  # This file
├── Docker-README.md           # Docker-specific documentation
└── *.ipynb                    # Jupyter notebooks (development/testing)
```

---

**Built with ❤️ for financial services document processing**
