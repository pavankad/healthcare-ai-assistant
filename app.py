"""
Flask EMR Application
A comprehensive Electronic Medical Records system for clinicians with PostgreSQL backend
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response
from datetime import datetime, timedelta
import json
import logging
import os
import uuid
from werkzeug.utils import secure_filename
from functools import wraps
from config import app_config
from database import initialize_database, DatabaseError, json_serializer
from services import (
    patient_service, medication_service, condition_service, diagnosis_service,
    clinical_note_service, allergy_service, immunization_service, appointment_service
)
# Import X-ray analysis functions
from xray_analysis_gpt4 import load_and_preprocess_image, analyze_xray_with_model, analyze_with_gpt4
# Import audio transcriber
from audio_transcriber import AudioTranscriber
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
    # Get patient_id from query parameter if provided
    patient_id = request.args.get('patient_id')
    return render_template('dashboard.html', selected_patient_id=patient_id)

@app.route('/add-patient')
@login_required
def add_patient():
    """Add new patient page"""
    return render_template('add_patient.html')

@app.route('/xray-analysis')
@login_required
def xray_analysis():
    """X-ray analysis page"""
    patient_id = request.args.get('patient_id')
    if not patient_id:
        return redirect(url_for('dashboard'))
    
    # Verify patient exists
    try:
        patient = patient_service.get_by_id(int(patient_id))
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('xray_analysis.html', patient=patient)
    except (ValueError, TypeError):
        flash('Invalid patient ID', 'error')
        return redirect(url_for('dashboard'))

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
# X-RAY ANALYSIS ENDPOINTS
# =============================================================================

def format_significant_findings(significant_findings):
    """Format significant findings for clinical note"""
    if not significant_findings:
        return "• No significant abnormalities detected (all pathology scores < 0.3)"
    
    formatted = []
    for pathology, score in significant_findings.items():
        severity = "HIGH" if score > 0.7 else "MODERATE" if score > 0.5 else "MILD"
        confidence = f"{score:.1%}"
        formatted.append(f"• {pathology.upper()}: {severity} confidence ({confidence})")
    
    return "\n".join(formatted)

def format_created_conditions(created_conditions):
    """Format created conditions for clinical note"""
    if not created_conditions:
        return "• No conditions automatically created (no significant findings)"
    
    formatted = []
    for cond in created_conditions:
        formatted.append(f"• {cond['condition']} - Confidence: {cond['score']:.1%}")
    
    return "\n".join(formatted)

def extract_recommendations_from_analysis(gpt4_analysis, significant_findings):
    """Extract or generate recommendations based on analysis"""
    recommendations = []
    
    # Check if GPT-4 analysis contains recommendations
    if "recommend" in gpt4_analysis.lower() or "suggest" in gpt4_analysis.lower():
        # Try to extract recommendations from GPT-4 analysis
        lines = gpt4_analysis.split('\n')
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'consider']):
                if line and not in_recommendations:
                    recommendations.append(f"• {line}")
                    in_recommendations = True
                elif line and in_recommendations:
                    recommendations.append(f"• {line}")
    
    # Add standard recommendations based on findings
    if significant_findings:
        recommendations.extend([
            "• Clinical correlation recommended for all AI-detected findings",
            "• Consider follow-up imaging if clinically indicated",
            "• Consult radiologist for definitive interpretation"
        ])
    else:
        recommendations.extend([
            "• Routine clinical follow-up as appropriate",
            "• No immediate imaging follow-up indicated based on AI analysis"
        ])
    
    # Add general recommendations
    recommendations.extend([
        "• Correlate with patient symptoms and physical examination",
        "• Review with patient's clinical history and previous imaging"
    ])
    
    return "\n".join(recommendations)

@app.route('/api/patients/<int:patient_id>/process_xray', methods=['POST'])
@login_required
@handle_database_error
def process_xray(patient_id):
    """Process X-ray image and store results as patient conditions"""
    
    # Check if patient exists
    try:
        patient_data = patient_service.get_by_id(patient_id)
        if not patient_data:
            return jsonify({'error': 'Patient not found'}), 404
    except Exception:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Check if file was uploaded
    if 'xray_image' not in request.files:
        return jsonify({'error': 'No X-ray image file provided'}), 400
    
    file = request.files['xray_image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'tiff', 'tif', 'dcm'}
    if not ('.' in file.filename and 
            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, TIFF, DICOM'}), 400
    
    try:
        # Create unique filename and save to xray-images directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{unique_id}{ext}"
        
        # Ensure xray-images directory exists
        xray_dir = os.path.join(os.getcwd(), 'xray-images')
        os.makedirs(xray_dir, exist_ok=True)
        
        filepath = os.path.join(xray_dir, unique_filename)
        file.save(filepath)
        
        logger.info(f"X-ray image saved: {filepath}")
        
        # Load environment variables for OpenAI
        import dotenv
        dotenv.load_dotenv(dotenv_path=".env.openai")
        
        # Process the X-ray image
        logger.info("Starting X-ray analysis...")
        
        # Step 1: Load and preprocess image
        img = load_and_preprocess_image(filepath)
        
        # Step 2: Analyze with torchxrayvision model
        xray_results = analyze_xray_with_model(img)
        
        # Step 3: Get patient info for context
        patient_context = f"Patient ID: {patient_id}\nName: {patient_data['first_name']} {patient_data['last_name']}\nAge: {patient_data.get('age', 'Unknown')}\nGender: {patient_data['gender']}"
        
        # Step 4: Analyze with GPT-4
        gpt4_analysis = analyze_with_gpt4(xray_results, patient_context)
        
        # Check if GPT-4 analysis was successful
        if gpt4_analysis.startswith("❌"):
            return jsonify({
                'error': 'X-ray analysis failed',
                'details': gpt4_analysis,
                'pathology_scores': {k: float(v) for k, v in xray_results.items()}
            }), 500
        
        # Step 5: Store results as conditions
        # Extract significant findings (scores > 0.3) and create conditions
        significant_findings = {k: v for k, v in xray_results.items() if float(v) > 0.3}
        
        created_conditions = []
        for pathology, score in significant_findings.items():
            condition_data = {
                'name': f"X-ray Finding: {pathology}",
                'icd_code': "Z87.891",  # Personal history of nicotine dependence - generic code for imaging findings
                'date_diagnosed': datetime.now().strftime('%Y-%m-%d'),
                'severity': 'Severe' if score > 0.7 else 'Moderate' if score > 0.5 else 'Mild',
                'status': 'Active'
            }
            
            condition_id = condition_service.create(patient_id, condition_data)
            created_conditions.append({
                'id': condition_id,
                'pathology': pathology,
                'score': float(score),
                'condition': condition_data['name']
            })
            
            logger.info(f"Created condition ID {condition_id} for {pathology} (score: {score:.4f})")
        
        # Step 6: Create a clinical note with the full GPT-4 analysis
        note_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'provider': 'AI X-ray Analysis System',
            'type': 'Radiology Report',
            'note': f"""AI ASSISTANT ANALYSIS

══════════════════════════════════════════════════════════════════════════════

X-RAY SOURCE:
• Image File: {unique_filename}
• Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Patient ID: {patient_id}
• Analysis Method: AI-Powered Deep Learning Model + GPT-4 Clinical Interpretation

══════════════════════════════════════════════════════════════════════════════

SUMMARIZED X-RAY RESULTS:
{format_significant_findings(significant_findings)}

══════════════════════════════════════════════════════════════════════════════

CLINICAL INTERPRETATION:
{gpt4_analysis}

══════════════════════════════════════════════════════════════════════════════

RECOMMENDED ACTIONS:
{extract_recommendations_from_analysis(gpt4_analysis, significant_findings)}

══════════════════════════════════════════════════════════════════════════════

AUTOMATED CONDITIONS CREATED:
{format_created_conditions(created_conditions)}

══════════════════════════════════════════════════════════════════════════════

⚠️  IMPORTANT DISCLAIMER:
This analysis is generated by AI and should be reviewed by a qualified radiologist.
All findings require clinical correlation and physician review before making
treatment decisions."""
        }
        
        note_id = clinical_note_service.create(patient_id, note_data)
        logger.info(f"Created clinical note ID {note_id} with X-ray analysis")
        
        return jsonify({
            'success': True,
            'message': 'X-ray processed successfully',
            'image_path': filepath,
            'pathology_scores': {k: float(v) for k, v in xray_results.items()},
            'significant_findings': {k: float(v) for k, v in significant_findings.items()},
            'gpt4_analysis': gpt4_analysis,
            'created_conditions': created_conditions,
            'clinical_note_id': note_id
        }), 201
        
    except ImportError as e:
        logger.error(f"Missing dependencies for X-ray analysis: {e}")
        return jsonify({
            'error': 'X-ray analysis dependencies not available',
            'details': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Error processing X-ray: {e}")
        return jsonify({
            'error': 'Failed to process X-ray',
            'details': str(e)
        }), 500
    
    finally:
        # Clean up the uploaded file if processing failed
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                # Keep the file for successful processing, only delete on failure
                pass
        except Exception:
            pass

# =============================================================================
# VOICE RECORDING API ENDPOINTS
# =============================================================================

# Global variable to store active recording sessions
active_recordings = {}

# Global AudioTranscriber instance for reusing Whisper model
global_audio_transcriber = None

def get_audio_transcriber():
    """Get or create the global AudioTranscriber instance"""
    global global_audio_transcriber
    if global_audio_transcriber is None:
        try:
            global_audio_transcriber = AudioTranscriber(model_size="base")
            logger.info("Initialized global AudioTranscriber with Whisper model")
        except Exception as e:
            logger.error(f"Failed to initialize AudioTranscriber: {e}")
            return None
    return global_audio_transcriber

@app.route('/api/voice/start-recording', methods=['POST'])
@login_required
@handle_database_error
def start_voice_recording():
    """Start a voice recording session for a patient"""
    data = request.get_json()
    patient_id = data.get('patient_id')
    provider = data.get('provider', 'Voice Transcription')
    
    if not patient_id:
        return jsonify({'error': 'Patient ID is required'}), 400
    
    try:
        # Check if patient exists
        patient_data = patient_service.get_by_id(patient_id)
        if not patient_data:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Create a new clinical note for the recording
        note_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'provider': provider,
            'type': 'Voice Transcription',
            'note': f'🎤 Voice transcription started at {datetime.now().strftime("%H:%M:%S")}\n\n'
        }
        
        note_id = clinical_note_service.create(patient_id, note_data)
        
        # Store the recording session
        session_id = str(uuid.uuid4())
        active_recordings[session_id] = {
            'patient_id': patient_id,
            'note_id': note_id,
            'provider': provider,
            'start_time': datetime.now(),
            'accumulated_text': note_data['note']
        }
        
        logger.info(f"Started voice recording session {session_id} for patient {patient_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'note_id': note_id,
            'message': 'Voice recording session started'
        }), 201
        
    except Exception as e:
        logger.error(f"Error starting voice recording: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/stop-recording', methods=['POST'])
@login_required
@handle_database_error
def stop_voice_recording():
    """Stop a voice recording session"""
    data = request.get_json()
    note_id = data.get('note_id')
    
    if not note_id:
        return jsonify({'error': 'Note ID is required'}), 400
    
    try:
        # Find and remove the recording session
        session_to_remove = None
        for session_id, session_data in active_recordings.items():
            if session_data['note_id'] == note_id:
                session_to_remove = session_id
                break
        
        if session_to_remove:
            session_data = active_recordings[session_to_remove]
            
            # Finalize the clinical note
            completion_text = f'\n🛑 Voice transcription completed at {datetime.now().strftime("%H:%M:%S")}'
            final_note = session_data['accumulated_text'] + completion_text
            
            update_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'provider': session_data['provider'],
                'type': 'Voice Transcription',
                'note': final_note
            }
            
            clinical_note_service.update(note_id, update_data)
            
            # Remove the session
            del active_recordings[session_to_remove]
            
            logger.info(f"Stopped voice recording session {session_to_remove}")
            
            return jsonify({
                'success': True,
                'message': 'Voice recording session stopped'
            }), 200
        else:
            return jsonify({'error': 'Recording session not found'}), 404
            
    except Exception as e:
        logger.error(f"Error stopping voice recording: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/transcription-stream/<note_id>')
@login_required
def transcription_stream(note_id):
    """Server-Sent Events stream for real-time transcription updates"""
    import time
    
    def generate():
        """Generate SSE stream"""
        last_update = time.time()
        
        while True:
            # Check if the recording session is still active
            session_active = any(
                session_data['note_id'] == note_id 
                for session_data in active_recordings.values()
            )
            
            if not session_active:
                # Session ended, send close event
                yield f"data: {json.dumps({'type': 'session_ended'})}\n\n"
                break
            
            # Send heartbeat every 30 seconds
            current_time = time.time()
            if current_time - last_update > 30:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                last_update = current_time
            
            time.sleep(1)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/api/voice/add-transcription', methods=['POST'])
@login_required
@handle_database_error
def add_transcription():
    """Add transcribed text to an active recording session"""
    data = request.get_json()
    note_id = data.get('note_id')
    transcription = data.get('transcription', '').strip()
    
    if not note_id or not transcription:
        return jsonify({'error': 'Note ID and transcription are required'}), 400
    
    try:
        # Find the recording session
        session_data = None
        for session_id, session_info in active_recordings.items():
            if session_info['note_id'] == note_id:
                session_data = session_info
                break
        
        if not session_data:
            return jsonify({'error': 'Recording session not found'}), 404
        
        # Add timestamp and new transcription
        timestamp = datetime.now().strftime('%H:%M:%S')
        new_text = f'[{timestamp}] {transcription}\n'
        session_data['accumulated_text'] += new_text
        
        # Update the clinical note
        update_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'provider': session_data['provider'],
            'type': 'Voice Transcription',
            'note': session_data['accumulated_text']
        }
        
        clinical_note_service.update(note_id, update_data)
        
        logger.info(f"Added transcription to note {note_id}: {transcription[:50]}...")
        
        return jsonify({
            'success': True,
            'message': 'Transcription added successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error adding transcription: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/transcribe-audio', methods=['POST'])
@login_required
@handle_database_error
def transcribe_audio():
    """Transcribe uploaded audio using the global AudioTranscriber"""
    try:
        # Check for uploaded audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        note_id = request.form.get('note_id')
        patient_id = request.form.get('patient_id')
        
        if not note_id or not patient_id:
            return jsonify({'error': 'Note ID and Patient ID are required'}), 400
        
        # Save the audio file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_chunk_{timestamp}_{uuid.uuid4().hex[:8]}.webm"
        
        # Create audio directory if it doesn't exist
        audio_dir = os.path.join(os.getcwd(), 'temp-audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        audio_path = os.path.join(audio_dir, filename)
        audio_file.save(audio_path)
        
        try:
            # Get the global AudioTranscriber instance
            transcriber = get_audio_transcriber()
            
            if transcriber is None:
                # Fallback to OpenAI Whisper API if local transcriber is not available
                logger.warning("Local AudioTranscriber not available, using OpenAI API fallback")
                return transcribe_with_openai_api(audio_path)
            
            # Use the existing AudioTranscriber to transcribe the file
            transcription = transcriber.transcribe_file(audio_path)
            
            logger.info(f"Transcribed audio chunk: {transcription[:100]}...")
            
            # Clean up the temporary file
            os.remove(audio_path)
            
            if transcription:
                return jsonify({
                    'success': True,
                    'transcription': transcription,
                    'method': 'local_whisper'
                }), 200
            else:
                return jsonify({
                    'error': 'Transcription returned empty result',
                    'transcription': ''
                }), 200
        
        except Exception as transcription_error:
            logger.error(f"Transcription error: {transcription_error}")
            # Clean up the temporary file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Try OpenAI API as fallback
            logger.warning("Local transcription failed, trying OpenAI API fallback")
            try:
                return transcribe_with_openai_api(audio_path)
            except Exception as fallback_error:
                logger.error(f"Fallback transcription also failed: {fallback_error}")
                return jsonify({
                    'error': 'Failed to transcribe audio',
                    'details': str(transcription_error)
                }), 500
    
    except Exception as e:
        logger.error(f"Audio transcription endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

def transcribe_with_openai_api(audio_path):
    """Fallback transcription using OpenAI Whisper API"""
    try:
        import openai
        import dotenv
        
        # Load OpenAI API key
        dotenv.load_dotenv(dotenv_path=".env.openai")
        client = openai.OpenAI()
        
        # Transcribe using OpenAI Whisper API
        with open(audio_path, 'rb') as audio_file_obj:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_obj,
                language="en"
            )
        
        transcription = transcript.text.strip()
        
        # Clean up the temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'method': 'openai_api'
        }), 200
        
    except Exception as api_error:
        logger.error(f"OpenAI Whisper API error: {api_error}")
        # Clean up the temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return jsonify({
            'error': 'Transcription service unavailable',
            'details': str(api_error)
        }), 500

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
