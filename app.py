"""
Flask EMR Application
A comprehensive Electronic Medical Records system for clinicians with PostgreSQL backend
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import json
import logging
from functools import wraps
from config import app_config
from database import initialize_database, DatabaseError, json_serializer
from services import (
    patient_service, medication_service, condition_service, diagnosis_service,
    clinical_note_service, allergy_service, immunization_service, appointment_service
)
import pdb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = app_config.secret_key
app.permanent_session_lifetime = timedelta(hours=app_config.session_timeout_hours)

# JSON encoder for datetime serialization
app.json.default = json_serializer

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def handle_database_error(func):
    """Decorator to handle database errors consistently"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
    return wrapper

@app.route('/')
def index():
    """Home route - redirect to dashboard if logged in, otherwise to login"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper password hashing)
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - EMR interface"""
    return render_template('dashboard.html')

@app.route('/add-patient')
@login_required
def add_patient():
    """Add new patient page"""
    return render_template('add_patient.html')

# =============================================================================
# PATIENT API ENDPOINTS
# =============================================================================

@app.route('/api/patients/search')
@login_required
@handle_database_error
def search_patients():
    """API endpoint to search for patients"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    results = patient_service.search(query)
    
    # Format results for frontend
    formatted_results = []
    for patient in results:
        formatted_results.append({
            'id': patient['id'],
            'name': f"{patient['first_name']} {patient['last_name']}",
            'dob': patient['date_of_birth'].isoformat() if patient['date_of_birth'] else '',
            'gender': patient['gender']
        })
    
    logger.info(f"Patient search for '{query}' returned {len(formatted_results)} results")
    return jsonify(formatted_results)

@app.route('/api/patients/<int:patient_id>')
@login_required
@handle_database_error
def get_patient(patient_id):
    """API endpoint to get complete patient details"""
    # Get patient demographics
    patient = patient_service.get_by_id(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get all related medical information
    patient_data = {
        'id': patient['id'],
        'name': f"{patient['first_name']} {patient['last_name']}",
        'demographics': dict(patient),
        'medications': medication_service.get_all(patient_id),
        'conditions': condition_service.get_all(patient_id),
        'diagnosis': diagnosis_service.get_all(patient_id),
        'clinical_notes': clinical_note_service.get_all(patient_id),
        'allergies': allergy_service.get_all(patient_id),
        'immunizations': immunization_service.get_all(patient_id),
        'appointments': appointment_service.get_all(patient_id)
    }
    
    logger.info(f"Retrieved complete patient data for patient {patient_id}")
    return jsonify(patient_data)

@app.route('/api/patients', methods=['POST'])
@login_required
@handle_database_error
def create_patient():
    """API endpoint to create a new patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    patient_id = patient_service.create(data)
    
    logger.info(f"Created new patient with ID {patient_id}")
    return jsonify({'success': True, 'patient_id': patient_id}), 201

@app.route('/api/patients/<int:patient_id>/demographics', methods=['PUT'])
@login_required
@handle_database_error
def update_patient_demographics(patient_id):
    """API endpoint to update patient demographics"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = patient_service.update(patient_id, data)
    
    if success:
        logger.info(f"Updated demographics for patient {patient_id}")
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update demographics'}), 500

# =============================================================================
# MEDICATION API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/medications', methods=['GET'])
@login_required
@handle_database_error
def get_medications(patient_id):
    """Get all medications for a patient"""
    medications = medication_service.get_all(patient_id)
    return jsonify(medications)

@app.route('/api/patients/<int:patient_id>/medications', methods=['POST'])
@login_required
@handle_database_error
def create_medication(patient_id):
    """Create a new medication record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    medication_id = medication_service.create(patient_id, data)
    return jsonify({'success': True, 'medication_id': medication_id}), 201

@app.route('/api/medications/<int:medication_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_medication(medication_id):
    """Update a medication record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = medication_service.update(medication_id, data)
    return jsonify({'success': success})

@app.route('/api/medications/<int:medication_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_medication(medication_id):
    """Delete a medication record"""
    success = medication_service.delete(medication_id)
    return jsonify({'success': success})

# =============================================================================
# CONDITION API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/conditions', methods=['GET'])
@login_required
@handle_database_error
def get_conditions(patient_id):
    """Get all conditions for a patient"""
    conditions = condition_service.get_all(patient_id)
    return jsonify(conditions)

@app.route('/api/patients/<int:patient_id>/conditions', methods=['POST'])
@login_required
@handle_database_error
def create_condition(patient_id):
    """Create a new condition record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    condition_id = condition_service.create(patient_id, data)
    return jsonify({'success': True, 'condition_id': condition_id}), 201

@app.route('/api/conditions/<int:condition_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_condition(condition_id):
    """Update a condition record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = condition_service.update(condition_id, data)
    return jsonify({'success': success})

@app.route('/api/conditions/<int:condition_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_condition(condition_id):
    """Delete a condition record"""
    success = condition_service.delete(condition_id)
    return jsonify({'success': success})

# =============================================================================
# DIAGNOSIS API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/diagnoses', methods=['GET'])
@login_required
@handle_database_error
def get_diagnoses(patient_id):
    """Get all diagnoses for a patient"""
    diagnoses = diagnosis_service.get_all(patient_id)
    return jsonify(diagnoses)

@app.route('/api/patients/<int:patient_id>/diagnoses', methods=['POST'])
@login_required
@handle_database_error
def create_diagnosis(patient_id):
    """Create a new diagnosis record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    diagnosis_id = diagnosis_service.create(patient_id, data)
    return jsonify({'success': True, 'diagnosis_id': diagnosis_id}), 201

@app.route('/api/diagnoses/<int:diagnosis_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_diagnosis(diagnosis_id):
    """Update a diagnosis record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = diagnosis_service.update(diagnosis_id, data)
    return jsonify({'success': success})

@app.route('/api/diagnoses/<int:diagnosis_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_diagnosis(diagnosis_id):
    """Delete a diagnosis record"""
    success = diagnosis_service.delete(diagnosis_id)
    return jsonify({'success': success})

# =============================================================================
# CLINICAL NOTES API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/clinical-notes', methods=['GET'])
@login_required
@handle_database_error
def get_clinical_notes(patient_id):
    """Get all clinical notes for a patient"""
    notes = clinical_note_service.get_all(patient_id)
    return jsonify(notes)

@app.route('/api/patient/<int:patient_id>/clinical_notes', methods=['GET'])
@login_required
@handle_database_error
def get_clinical_notes_for_polling(patient_id):
    """Get clinical notes for polling - returns in expected format"""
    notes = clinical_note_service.get_all(patient_id)
    return jsonify({'success': True, 'data': notes})

@app.route('/api/patients/<int:patient_id>/clinical-notes', methods=['POST'])
#@login_required
@handle_database_error
def create_clinical_note(patient_id):
    """Create a new clinical note record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    note_id = clinical_note_service.create(patient_id, data)
    return jsonify({'success': True, 'note_id': note_id}), 201

@app.route('/api/clinical-notes/<int:note_id>', methods=['PUT'])
#@login_required
@handle_database_error
def update_clinical_note(note_id):
    """Update a clinical note record"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = clinical_note_service.update(note_id, data)
    return jsonify({'success': success})

@app.route('/api/clinical-notes/<int:note_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_clinical_note(note_id):
    """Delete a clinical note record"""
    success = clinical_note_service.delete(note_id)
    return jsonify({'success': success})

# =============================================================================
# ALLERGY API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/allergies', methods=['GET'])
@login_required
@handle_database_error
def get_allergies(patient_id):
    """Get all allergies for a patient"""
    allergies = allergy_service.get_all(patient_id)
    return jsonify(allergies)

@app.route('/api/patients/<int:patient_id>/allergies', methods=['POST'])
@login_required
@handle_database_error
def create_allergy(patient_id):
    """Create a new allergy record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    allergy_id = allergy_service.create(patient_id, data)
    return jsonify({'success': True, 'allergy_id': allergy_id}), 201

@app.route('/api/allergies/<int:allergy_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_allergy(allergy_id):
    """Update an allergy record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = allergy_service.update(allergy_id, data)
    return jsonify({'success': success})

@app.route('/api/allergies/<int:allergy_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_allergy(allergy_id):
    """Delete an allergy record"""
    success = allergy_service.delete(allergy_id)
    return jsonify({'success': success})

# =============================================================================
# IMMUNIZATION API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/immunizations', methods=['GET'])
@login_required
@handle_database_error
def get_immunizations(patient_id):
    """Get all immunizations for a patient"""
    immunizations = immunization_service.get_all(patient_id)
    return jsonify(immunizations)

@app.route('/api/patients/<int:patient_id>/immunizations', methods=['POST'])
@login_required
@handle_database_error
def create_immunization(patient_id):
    """Create a new immunization record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    immunization_id = immunization_service.create(patient_id, data)
    return jsonify({'success': True, 'immunization_id': immunization_id}), 201

@app.route('/api/immunizations/<int:immunization_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_immunization(immunization_id):
    """Update an immunization record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = immunization_service.update(immunization_id, data)
    return jsonify({'success': success})

@app.route('/api/immunizations/<int:immunization_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_immunization(immunization_id):
    """Delete an immunization record"""
    success = immunization_service.delete(immunization_id)
    return jsonify({'success': success})

# =============================================================================
# APPOINTMENT API ENDPOINTS
# =============================================================================

@app.route('/api/patients/<int:patient_id>/appointments', methods=['GET'])
@login_required
@handle_database_error
def get_appointments(patient_id):
    """Get all appointments for a patient"""
    appointments = appointment_service.get_all(patient_id)
    return jsonify(appointments)

@app.route('/api/patients/<int:patient_id>/appointments', methods=['POST'])
@login_required
@handle_database_error
def create_appointment(patient_id):
    """Create a new appointment record for a patient"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    appointment_id = appointment_service.create(patient_id, data)
    return jsonify({'success': True, 'appointment_id': appointment_id}), 201

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
@handle_database_error
def update_appointment(appointment_id):
    """Update an appointment record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = appointment_service.update(appointment_id, data)
    return jsonify({'success': success})

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
@handle_database_error
def delete_appointment(appointment_id):
    """Delete an appointment record"""
    success = appointment_service.delete(appointment_id)
    return jsonify({'success': success})

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

def init_app():
    """Initialize the application"""
    try:
        # Initialize database
        initialize_database()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

if __name__ == '__main__':
    init_app()
    app.run(debug=app_config.debug, host=app_config.host, port=app_config.port)
