# EMR System - Electronic Medical Records

A comprehensive Flask-based Electronic Medical Records (EMR) Single Page Application with PostgreSQL backend, designed for healthcare clinicians to manage patient information efficiently.

## Features

### Authentication
- Secure login system (Username: `admin`, Password: `admin`)
- Session management with automatic timeout
- User authentication required for all features

### Patient Management
- **Patient Search**: Real-time search functionality to find patients by name
- **Patient Creation**: Add new patients with complete demographics
- **Patient Selection**: Easy patient selection from search results
- **Comprehensive Patient Information**:

#### Demographics
- Personal information (name, DOB, gender, contact details)
- Address and emergency contact information
- Insurance details

#### Medical Information (Organized in separate API endpoints)
1. **Medications**: Current and past medications with dosage, frequency, and prescribing information
2. **Conditions**: Medical conditions with ICD codes, severity, and status
3. **Diagnosis**: Diagnosis history with primary/secondary diagnoses and provider notes
4. **Clinical Notes**: Progress notes, consultations, and assessments
5. **Allergies**: Known allergies with severity levels and reactions
6. **Immunizations**: Vaccination records with dates and lot numbers
7. **Appointments**: Scheduled and past appointments with providers

### Data Management
- **Create**: Add new entries to any medical section
- **Read**: View all patient information in organized sections
- **Update**: Edit existing medical information
- **Delete**: Remove outdated or incorrect entries
- **PostgreSQL Backend**: Secure, scalable database with proper indexing

### API Endpoints
Each medical section has dedicated RESTful API endpoints:
- `GET /api/patients/{id}/medications` - Get medications
- `POST /api/patients/{id}/medications` - Create medication
- `PUT /api/medications/{id}` - Update medication
- `DELETE /api/medications/{id}` - Delete medication
- Similar endpoints for conditions, diagnoses, clinical notes, allergies, immunizations, and appointments

### User Interface
- Modern, responsive design using Bootstrap 5
- Intuitive single-page application experience
- Real-time search and filtering
- Modal dialogs for data entry and editing
- Visual indicators for status and severity levels
- Professional medical interface with appropriate color coding

### AI-Powered Features
- **X-Ray Analysis**: AI-powered chest X-ray interpretation using TorchXRayVision and GPT-4
  - Upload DICOM or image files for analysis
  - Automated pathology detection and scoring
  - Structured clinical reports with findings and recommendations
  - Integration with patient medical records

- **Voice Recording & Transcription**: Real-time speech-to-text for clinical notes
  - Microphone button in Medical Information section
  - Real-time transcription using OpenAI Whisper
  - Automatic clinical note creation during recording
  - Toggle on/off recording functionality
  - See [VOICE_RECORDING.md](VOICE_RECORDING.md) for detailed usage instructions

## Technology Stack

- **Backend**: Python Flask with PostgreSQL
- **Database**: PostgreSQL with connection pooling
- **Frontend**: HTML5, CSS3, JavaScript (jQuery)
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome 6
- **Database ORM**: Direct SQL with psycopg2 for optimal performance

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or download the project**
   ```bash
   cd healthcare-ai-assistant
   ```

2. **Install PostgreSQL**
   ```bash
   # On macOS with Homebrew
   brew install postgresql
   brew services start postgresql
   
   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   
   # On Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

3. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your database configuration
   ```

6. **Set up the database**
   ```bash
   python setup_database.py
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. **Access the application**
   - Open your web browser
   - Navigate to: `http://localhost:5000`
   - Login with credentials: Username: `admin`, Password: `admin`

## Application Structure

```
healthcare-ai-assistant/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/            # HTML templates
    ├── base.html         # Base template with common elements
    ├── login.html        # Login page
    ├── dashboard.html    # Main EMR dashboard
    ├── 404.html          # 404 error page
    └── 500.html          # 500 error page
```

## Sample Data

The application comes pre-loaded with sample patient data including:

### Patient 1: John Doe
- Demographics: Male, DOB: 1985-03-15
- Conditions: Hypertension, Type 2 Diabetes
- Medications: Lisinopril, Metformin
- Full medical history with allergies, immunizations, and appointments

### Patient 2: Jane Smith
- Demographics: Female, DOB: 1978-08-22
- Conditions: Hyperlipidemia
- Medications: Atorvastatin
- Complete medical records

## Security Features

- Session-based authentication
- Session timeout after 8 hours of inactivity
- Input validation and error handling
- Secure data handling practices
- Protection against common web vulnerabilities

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Process login credentials
- `GET /logout` - User logout

### Patient Data
- `GET /api/search_patients?q=<query>` - Search patients
- `GET /api/patient/<patient_id>` - Get patient details
- `POST /api/patient/<patient_id>/<section>` - Update patient section

### Dashboard
- `GET /dashboard` - Main EMR interface

## Usage Instructions

### Logging In
1. Open the application in your browser
2. Use the provided credentials (admin/admin)
3. Click "Login" to access the EMR system

### Searching for Patients
1. Use the search box on the dashboard
2. Type at least 2 characters of the patient's name
3. Click on a patient from the search results

### Viewing Patient Information
- Patient information is organized in clear sections
- Use tabs to navigate between different medical information categories
- All information is displayed in an easy-to-read format

### Editing Patient Information
1. Click the "Edit" button on any section or item
2. Fill in the modal form with updated information
3. Click "Save" to update the information
4. The changes will be reflected immediately

### Adding New Information
1. Click the "Add" button in any medical section
2. Fill in the required information in the modal form
3. Click "Save" to add the new entry

### Deleting Information
1. Click the "Delete" button on any item
2. Confirm the deletion in the confirmation dialog
3. The item will be removed immediately

## Customization

### Adding New Patient Sections
1. Update the `SAMPLE_PATIENTS` dictionary in `app.py`
2. Add corresponding display functions in `dashboard.html`
3. Create form fields for the new section in the modal

### Database Integration
Replace the in-memory `SAMPLE_PATIENTS` dictionary with actual database calls:
1. Choose a database (PostgreSQL, MySQL, SQLite)
2. Install appropriate database drivers
3. Update the API endpoints to use database queries
4. Implement proper data validation and sanitization

### Authentication Enhancement
- Integrate with existing hospital authentication systems
- Add role-based access control
- Implement password complexity requirements
- Add multi-factor authentication

## Production Considerations

### Security
- Change the secret key in production
- Use environment variables for sensitive configuration
- Implement HTTPS
- Add rate limiting and input validation
- Regular security audits

### Database
- Use a production database (PostgreSQL recommended)
- Implement proper backup strategies
- Add database connection pooling
- Implement audit logging for compliance

### Performance
- Add caching for frequently accessed data
- Implement pagination for large datasets
- Optimize database queries
- Add CDN for static assets

### Compliance
- Ensure HIPAA compliance for patient data
- Implement audit trails
- Add data encryption at rest and in transit
- Regular compliance reviews

## Troubleshooting

### Common Issues

1. **Application won't start**
   - Check Python version (3.8+)
   - Verify all dependencies are installed
   - Check for port conflicts (default: 5000)

2. **Login issues**
   - Verify credentials: admin/admin
   - Check browser cookies are enabled
   - Clear browser cache if needed

3. **Search not working**
   - Ensure at least 2 characters are entered
   - Check browser JavaScript is enabled
   - Verify network connectivity

### Logs
Application logs are printed to the console. Check for error messages if issues occur.

## License

This is a demonstration EMR system for educational and development purposes. For production use in healthcare environments, ensure compliance with all applicable regulations including HIPAA, GDPR, and local healthcare data protection laws.

## Support

For issues or questions about this EMR system, please review the code comments and documentation. This is a demonstration application designed to showcase EMR functionality and development practices.