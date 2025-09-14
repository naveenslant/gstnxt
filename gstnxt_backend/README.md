# GST Next Backend

A FastAPI-based backend service for GST file analysis and processing.

## Features

- **Authentication System**: JWT-based authentication with demo login
- **GSTIN Validation**: Comprehensive GSTIN validation with check digit verification
- **File Processing**: Support for GSTR1/GSTR2A Excel and ZIP file uploads
- **GST Analysis**: Month-wise data compilation and formatted Excel output
- **Project Management**: Organize GST data by projects and financial years

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment (recommended)

### Installation

1. **Clone and setup**:
   ```bash
   cd gstnxt_backend
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database setup**:
   - Create PostgreSQL database: `gstnxt`
   - Update database URL in `.env` file
   - Tables will be created automatically on first run

4. **Configuration**:
   ```bash
   copy .env.example .env
   # Edit .env with your database credentials
   ```

5. **Start server**:
   ```bash
   # Option 1: Direct command
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   
   # Option 2: Use batch script (Windows)
   start_server.bat
   ```

6. **Access API**:
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/demo-login` - Demo user login

### GSTIN Validation
- `POST /api/gstin/validate` - Validate GSTIN number
- `GET /api/gstin/validation-history` - Get validation history

### Project Management
- `POST /api/projects/create` - Create new GST project
- `GET /api/projects/list` - List user projects
- `GET /api/projects/{project_id}` - Get project details
- `DELETE /api/projects/{project_id}` - Delete project

### File Management
- `POST /api/files/upload/{project_id}` - Upload GST files
- `GET /api/files/list/{project_id}` - List uploaded files
- `DELETE /api/files/file/{file_id}` - Delete file
- `POST /api/files/analyze/{project_id}` - Trigger analysis
- `GET /api/files/analysis/{project_id}` - Get analysis results

## File Format Support

### Supported Files
- **GSTR1 Excel files**: Pattern `*GSTR1*MMYYYY*.xlsx`
- **GSTR2A Excel files**: Pattern `*GSTR2A*MMYYYY*.xlsx`
- **ZIP archives**: Containing Excel files

### File Naming Convention
Files must follow the naming pattern:
- `CompanyName_GSTR1_042024_Data.xlsx` (April 2024 GSTR1)
- `ABC_Ltd_GSTR2A_032024.xlsx` (March 2024 GSTR2A)

## Project Structure

```
gstnxt_backend/
├── app/
│   ├── api/
│   │   └── routes/          # API route handlers
│   ├── services/            # Business logic services
│   ├── models.py           # Database models
│   ├── database.py         # Database configuration
│   └── __init__.py
├── uploads/                # File upload directory
├── outputs/                # Analysis output directory
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
└── start_server.bat       # Windows startup script
```

## Development

### Database Models
- `User`: User authentication and profile
- `GSTProject`: Project organization
- `FileUpload`: Uploaded file tracking
- `AnalysisResult`: Analysis results and outputs
- `GSTINValidation`: GSTIN validation history

### Services
- `AuthService`: JWT authentication and user management
- `GSTINValidator`: GSTIN number validation
- `FileValidationService`: File upload and validation
- `GSTAnalysisService`: GST data analysis and Excel generation

## Production Deployment

1. **Environment**:
   - Set `DEBUG=False` in production
   - Use strong JWT secret keys
   - Configure proper CORS origins
   - Use production PostgreSQL database

2. **Security**:
   - Enable HTTPS
   - Set secure database credentials
   - Configure firewall rules
   - Regular security updates

3. **Monitoring**:
   - Application logs
   - Database performance
   - File storage usage
   - API response times

## License

Proprietary software for SlantAxiom GST solutions.
