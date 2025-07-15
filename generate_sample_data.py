#!/usr/bin/env python3
"""
Generate comprehensive sample data for EMR system
Creates 10 patients with complete medical records including:
- Demographics
- Medications
- Conditions
- Diagnoses
- Clinical Notes
- Allergies
- Immunizations
- Appointments
"""

import random
import logging
from datetime import datetime, date, timedelta
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data pools
FIRST_NAMES_MALE = [
    'James', 'Robert', 'John', 'Michael', 'David', 'William', 'Richard', 'Charles', 'Joseph', 'Thomas',
    'Christopher', 'Daniel', 'Paul', 'Mark', 'Donald', 'Steven', 'Andrew', 'Joshua', 'Kenneth', 'Kevin'
]

FIRST_NAMES_FEMALE = [
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
    'Lisa', 'Nancy', 'Betty', 'Helen', 'Sandra', 'Donna', 'Carol', 'Ruth', 'Sharon', 'Michelle'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
]

CITIES = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
    'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco',
    'Indianapolis', 'Seattle', 'Denver', 'Washington DC'
]

STATES = [
    'NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'FL', 'OH', 'NC', 'WA', 'CO', 'DC'
]

MEDICATIONS = [
    {'name': 'Lisinopril', 'dosages': ['5mg', '10mg', '20mg'], 'frequencies': ['Once daily', 'Twice daily']},
    {'name': 'Metformin', 'dosages': ['500mg', '850mg', '1000mg'], 'frequencies': ['Once daily', 'Twice daily']},
    {'name': 'Atorvastatin', 'dosages': ['10mg', '20mg', '40mg'], 'frequencies': ['Once daily']},
    {'name': 'Amlodipine', 'dosages': ['2.5mg', '5mg', '10mg'], 'frequencies': ['Once daily']},
    {'name': 'Omeprazole', 'dosages': ['20mg', '40mg'], 'frequencies': ['Once daily', 'Twice daily']},
    {'name': 'Hydrochlorothiazide', 'dosages': ['12.5mg', '25mg'], 'frequencies': ['Once daily']},
    {'name': 'Aspirin', 'dosages': ['81mg', '325mg'], 'frequencies': ['Once daily']},
    {'name': 'Levothyroxine', 'dosages': ['25mcg', '50mcg', '75mcg', '100mcg'], 'frequencies': ['Once daily']},
    {'name': 'Sertraline', 'dosages': ['25mg', '50mg', '100mg'], 'frequencies': ['Once daily']},
    {'name': 'Losartan', 'dosages': ['25mg', '50mg', '100mg'], 'frequencies': ['Once daily']}
]

CONDITIONS = [
    {'name': 'Hypertension', 'icd_code': 'I10', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Type 2 Diabetes', 'icd_code': 'E11', 'severities': ['Controlled', 'Moderate', 'Severe']},
    {'name': 'Hyperlipidemia', 'icd_code': 'E78.5', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Obesity', 'icd_code': 'E66.9', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Depression', 'icd_code': 'F32.9', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Asthma', 'icd_code': 'J45.9', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Hypothyroidism', 'icd_code': 'E03.9', 'severities': ['Mild', 'Moderate']},
    {'name': 'Osteoarthritis', 'icd_code': 'M19.9', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'GERD', 'icd_code': 'K21.9', 'severities': ['Mild', 'Moderate', 'Severe']},
    {'name': 'Anxiety Disorder', 'icd_code': 'F41.9', 'severities': ['Mild', 'Moderate', 'Severe']}
]

ALLERGIES = [
    {'allergen': 'Penicillin', 'reactions': ['Rash', 'Hives', 'Swelling'], 'severities': ['Mild', 'Moderate', 'Severe']},
    {'allergen': 'Shellfish', 'reactions': ['Swelling', 'Difficulty breathing', 'Anaphylaxis'], 'severities': ['Moderate', 'Severe']},
    {'allergen': 'Latex', 'reactions': ['Contact dermatitis', 'Rash'], 'severities': ['Mild', 'Moderate']},
    {'allergen': 'Sulfa drugs', 'reactions': ['Rash', 'Nausea'], 'severities': ['Mild', 'Moderate']},
    {'allergen': 'Nuts', 'reactions': ['Swelling', 'Breathing difficulty'], 'severities': ['Moderate', 'Severe']},
    {'allergen': 'Iodine', 'reactions': ['Rash', 'Swelling'], 'severities': ['Mild', 'Moderate']},
    {'allergen': 'Eggs', 'reactions': ['Hives', 'Digestive issues'], 'severities': ['Mild', 'Moderate']},
    {'allergen': 'Dust mites', 'reactions': ['Sneezing', 'Congestion'], 'severities': ['Mild']},
    {'allergen': 'Pollen', 'reactions': ['Sneezing', 'Itchy eyes'], 'severities': ['Mild', 'Moderate']},
    {'allergen': 'Codeine', 'reactions': ['Nausea', 'Dizziness'], 'severities': ['Mild', 'Moderate']}
]

VACCINES = [
    {'vaccine': 'COVID-19', 'lot_prefixes': ['CV', 'PF', 'MD']},
    {'vaccine': 'Influenza', 'lot_prefixes': ['FL', 'IN', 'FU']},
    {'vaccine': 'Tetanus', 'lot_prefixes': ['TT', 'TD', 'TP']},
    {'vaccine': 'Pneumonia', 'lot_prefixes': ['PN', 'PC', 'PP']},
    {'vaccine': 'Shingles', 'lot_prefixes': ['SH', 'ZO', 'HZ']},
    {'vaccine': 'Hepatitis B', 'lot_prefixes': ['HB', 'HP', 'HE']},
    {'vaccine': 'MMR', 'lot_prefixes': ['MM', 'MR', 'MS']},
    {'vaccine': 'HPV', 'lot_prefixes': ['HP', 'GR', 'CV']}
]

PROVIDERS = [
    'Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Jones',
    'Dr. Garcia', 'Dr. Miller', 'Dr. Davis', 'Dr. Rodriguez', 'Dr. Martinez',
    'Dr. Wilson', 'Dr. Anderson', 'Dr. Taylor', 'Dr. Thomas', 'Dr. Moore'
]

APPOINTMENT_TYPES = [
    'Annual Physical', 'Follow-up', 'Consultation', 'Urgent Care', 'Specialist Referral',
    'Lab Review', 'Procedure', 'Screening', 'Preventive Care', 'Chronic Care Management'
]

APPOINTMENT_STATUSES = ['Scheduled', 'Completed', 'Cancelled', 'No-show']

NOTE_TYPES = ['Progress Note', 'Consultation', 'Assessment', 'Discharge Summary', 'History']

def generate_phone():
    """Generate a random phone number"""
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

def generate_date_in_range(start_years_ago, end_years_ago):
    """Generate a random date within a range"""
    start_date = datetime.now() - timedelta(days=start_years_ago * 365)
    end_date = datetime.now() - timedelta(days=end_years_ago * 365)
    
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return (start_date + timedelta(days=random_days)).date()

def generate_recent_date(max_days_ago=365):
    """Generate a recent date within specified days"""
    days_ago = random.randint(1, max_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).date()

def generate_future_date(max_days_ahead=180):
    """Generate a future date for appointments"""
    days_ahead = random.randint(1, max_days_ahead)
    return (datetime.now() + timedelta(days=days_ahead)).date()

def generate_patient_data():
    """Generate comprehensive data for one patient"""
    # Generate demographics
    gender = random.choice(['Male', 'Female'])
    first_name = random.choice(FIRST_NAMES_MALE if gender == 'Male' else FIRST_NAMES_FEMALE)
    last_name = random.choice(LAST_NAMES)
    
    # Generate age between 18 and 85
    age = random.randint(18, 85)
    birth_date = generate_date_in_range(age + 1, age)
    
    city = random.choice(CITIES)
    state = random.choice(STATES)
    
    demographics = {
        'first_name': first_name,
        'last_name': last_name,
        'date_of_birth': birth_date,
        'gender': gender,
        'phone': generate_phone(),
        'email': f"{first_name.lower()}.{last_name.lower()}@email.com",
        'address': f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'First', 'Second'])} {random.choice(['St', 'Ave', 'Dr', 'Ln'])}, {city}, {state} {random.randint(10000, 99999)}",
        'emergency_contact': f"{random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)} {last_name} - {generate_phone()}",
        'insurance': f"{random.choice(['BlueCross BlueShield', 'Aetna', 'Cigna', 'United Healthcare', 'Kaiser Permanente'])} - Policy #{random.choice(['BC', 'AE', 'CG', 'UH', 'KP'])}{random.randint(100000, 999999)}"
    }
    
    # Generate medical data
    num_conditions = random.randint(1, 4)
    patient_conditions = random.sample(CONDITIONS, num_conditions)
    
    num_medications = random.randint(1, 5)
    patient_medications = random.sample(MEDICATIONS, num_medications)
    
    num_allergies = random.randint(0, 3)
    patient_allergies = random.sample(ALLERGIES, num_allergies)
    
    num_vaccines = random.randint(2, 6)
    patient_vaccines = random.sample(VACCINES, num_vaccines)
    
    return {
        'demographics': demographics,
        'conditions': patient_conditions,
        'medications': patient_medications,
        'allergies': patient_allergies,
        'vaccines': patient_vaccines
    }

def insert_patient_with_medical_data(patient_data):
    """Insert a patient and all their medical data"""
    try:
        # Insert patient demographics
        patient_id = db.execute_query(
            """INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, 
               address, emergency_contact, insurance) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                patient_data['demographics']['first_name'],
                patient_data['demographics']['last_name'],
                patient_data['demographics']['date_of_birth'],
                patient_data['demographics']['gender'],
                patient_data['demographics']['phone'],
                patient_data['demographics']['email'],
                patient_data['demographics']['address'],
                patient_data['demographics']['emergency_contact'],
                patient_data['demographics']['insurance']
            )
        )[0]['id']
        
        logger.info(f"Inserted patient: {patient_data['demographics']['first_name']} {patient_data['demographics']['last_name']} (ID: {patient_id})")
        
        # Insert conditions
        for condition in patient_data['conditions']:
            date_diagnosed = generate_recent_date(1825)  # Within last 5 years
            db.execute_query(
                """INSERT INTO conditions (patient_id, name, icd_code, status, date_diagnosed, severity)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (patient_id, condition['name'], condition['icd_code'], 'Active', 
                 date_diagnosed, random.choice(condition['severities'])),
                fetch=False
            )
        
        # Insert medications
        for medication in patient_data['medications']:
            start_date = generate_recent_date(730)  # Within last 2 years
            db.execute_query(
                """INSERT INTO medications (patient_id, name, dosage, frequency, start_date, 
                   prescribing_doctor, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (patient_id, medication['name'], random.choice(medication['dosages']),
                 random.choice(medication['frequencies']), start_date,
                 random.choice(PROVIDERS), 'Active'),
                fetch=False
            )
        
        # Insert allergies
        for allergy in patient_data['allergies']:
            date_identified = generate_recent_date(3650)  # Within last 10 years
            db.execute_query(
                """INSERT INTO allergies (patient_id, allergen, reaction, severity, date_identified)
                   VALUES (%s, %s, %s, %s, %s)""",
                (patient_id, allergy['allergen'], random.choice(allergy['reactions']),
                 random.choice(allergy['severities']), date_identified),
                fetch=False
            )
        
        # Insert immunizations
        for vaccine in patient_data['vaccines']:
            date_administered = generate_recent_date(1095)  # Within last 3 years
            lot_number = f"{random.choice(vaccine['lot_prefixes'])}{random.randint(100000, 999999)}"
            db.execute_query(
                """INSERT INTO immunizations (patient_id, vaccine, date_administered, provider, lot_number)
                   VALUES (%s, %s, %s, %s, %s)""",
                (patient_id, vaccine['vaccine'], date_administered,
                 random.choice(PROVIDERS), lot_number),
                fetch=False
            )
        
        # Insert diagnoses
        num_diagnoses = random.randint(1, 3)
        for _ in range(num_diagnoses):
            diagnosis_date = generate_recent_date(365)
            primary_diagnosis = random.choice(patient_data['conditions'])['name']
            secondary_diagnosis = random.choice(['', random.choice(patient_data['conditions'])['name']])
            if secondary_diagnosis == primary_diagnosis:
                secondary_diagnosis = ''
            
            db.execute_query(
                """INSERT INTO diagnoses (patient_id, date, primary_diagnosis, secondary_diagnosis, 
                   provider, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (patient_id, diagnosis_date, primary_diagnosis, secondary_diagnosis,
                 random.choice(PROVIDERS), f"Patient showing {random.choice(['improvement', 'stable condition', 'good response to treatment'])} with current treatment plan."),
                fetch=False
            )
        
        # Insert clinical notes
        num_notes = random.randint(2, 5)
        for _ in range(num_notes):
            note_date = generate_recent_date(365)
            note_type = random.choice(NOTE_TYPES)
            notes = [
                f"Patient reports feeling {random.choice(['well', 'better', 'stable', 'improved'])}. {random.choice(['Continue current medications', 'Adjusting dosage as needed', 'Monitoring closely', 'No changes to treatment plan'])}.",
                f"{random.choice(['Blood pressure', 'Blood sugar', 'Cholesterol levels', 'Vital signs'])} {random.choice(['stable', 'improving', 'within normal range', 'well controlled'])}. {random.choice(['Patient compliant with medication', 'Good adherence to treatment', 'Following dietary recommendations'])}.",
                f"Follow-up {random.choice(['in 3 months', 'in 6 months', 'as needed', 'in 1 month'])}. {random.choice(['Continue monitoring', 'Lab work ordered', 'Referral discussed', 'Patient education provided'])}."
            ]
            
            db.execute_query(
                """INSERT INTO clinical_notes (patient_id, date, provider, type, note)
                   VALUES (%s, %s, %s, %s, %s)""",
                (patient_id, note_date, random.choice(PROVIDERS), note_type, random.choice(notes)),
                fetch=False
            )
        
        # Insert appointments
        num_appointments = random.randint(2, 4)
        for _ in range(num_appointments):
            # Mix of past and future appointments
            if random.choice([True, False]):
                appt_date = generate_recent_date(180)  # Past appointment
                status = random.choice(['Completed', 'Cancelled', 'No-show'])
            else:
                appt_date = generate_future_date(180)  # Future appointment
                status = 'Scheduled'
            
            appt_time = f"{random.randint(8, 17)}:{random.choice(['00', '15', '30', '45'])}"
            appt_type = random.choice(APPOINTMENT_TYPES)
            
            db.execute_query(
                """INSERT INTO appointments (patient_id, date, time, provider, type, status, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (patient_id, appt_date, appt_time, random.choice(PROVIDERS), 
                 appt_type, status, f"{appt_type} appointment for {random.choice(['routine care', 'follow-up', 'assessment', 'monitoring'])}"),
                fetch=False
            )
        
        return patient_id
        
    except Exception as e:
        logger.error(f"Failed to insert patient data: {e}")
        raise

def generate_and_insert_patients(num_patients=10):
    """Generate and insert multiple patients with complete medical records"""
    logger.info(f"Starting generation of {num_patients} patients with complete medical records...")
    
    # Clear existing sample data (optional)
    clear_existing = input("Clear existing patient data? (y/n): ").lower().strip()
    if clear_existing == 'y':
        try:
            # Delete in reverse order of dependencies
            db.execute_query("DELETE FROM appointments", fetch=False)
            db.execute_query("DELETE FROM immunizations", fetch=False)
            db.execute_query("DELETE FROM allergies", fetch=False)
            db.execute_query("DELETE FROM clinical_notes", fetch=False)
            db.execute_query("DELETE FROM diagnoses", fetch=False)
            db.execute_query("DELETE FROM conditions", fetch=False)
            db.execute_query("DELETE FROM medications", fetch=False)
            db.execute_query("DELETE FROM patients", fetch=False)
            logger.info("Existing patient data cleared")
        except Exception as e:
            logger.error(f"Failed to clear existing data: {e}")
    
    patients_created = 0
    for i in range(num_patients):
        try:
            patient_data = generate_patient_data()
            patient_id = insert_patient_with_medical_data(patient_data)
            patients_created += 1
            logger.info(f"Patient {i+1}/{num_patients} created successfully (ID: {patient_id})")
        except Exception as e:
            logger.error(f"Failed to create patient {i+1}: {e}")
    
    logger.info(f"Successfully created {patients_created} patients with complete medical records")
    return patients_created

if __name__ == "__main__":
    try:
        # Generate 10 patients with comprehensive medical data
        generate_and_insert_patients(10)
        logger.info("Sample data generation completed successfully!")
    except Exception as e:
        logger.error(f"Sample data generation failed: {e}")
