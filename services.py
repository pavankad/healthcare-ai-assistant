"""
CRUD service classes for EMR system
Implements secure database operations for all patient data sections
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging
from database import db, DatabaseError
import pdb

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common CRUD operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def _format_where_clause(self, conditions: Dict[str, Any]) -> tuple:
        """Format WHERE clause with parameters for safe SQL execution"""
        if not conditions:
            return "", ()
        
        where_parts = []
        params = []
        
        for key, value in conditions.items():
            where_parts.append(f"{key} = %s")
            params.append(value)
        
        where_clause = " WHERE " + " AND ".join(where_parts)
        return where_clause, tuple(params)
    
    def get_all(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all records for a patient"""
        query = f"SELECT * FROM {self.table_name} WHERE patient_id = %s ORDER BY created_at DESC"
        try:
            return db.execute_query(query, (patient_id,))
        except Exception as e:
            logger.error(f"Failed to get all {self.table_name} for patient {patient_id}: {e}")
            raise DatabaseError(f"Failed to retrieve {self.table_name}")
    
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific record by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        try:
            results = db.execute_query(query, (record_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get {self.table_name} record {record_id}: {e}")
            raise DatabaseError(f"Failed to retrieve {self.table_name} record")
    
    def delete(self, record_id: int) -> bool:
        """Delete a record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        try:
            db.execute_query(query, (record_id,), fetch=False)
            logger.info(f"Deleted {self.table_name} record {record_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {self.table_name} record {record_id}: {e}")
            raise DatabaseError(f"Failed to delete {self.table_name} record")

class PatientService(BaseService):
    """Service for patient demographics operations"""
    
    def __init__(self):
        super().__init__("patients")
    
    def create(self, patient_data: Dict[str, Any]) -> int:
        """Create a new patient record"""
        query = """
            INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, 
                                address, emergency_contact, insurance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('date_of_birth'),
            patient_data.get('gender'),
            patient_data.get('phone'),
            patient_data.get('email'),
            patient_data.get('address'),
            patient_data.get('emergency_contact'),
            patient_data.get('insurance')
        )
        
        try:
            result = db.execute_query(query, params)
            patient_id = result[0]['id']
            logger.info(f"Created patient record with ID {patient_id}")
            return patient_id
        except Exception as e:
            logger.error(f"Failed to create patient: {e}")
            raise DatabaseError("Failed to create patient record")
    
    def update(self, patient_id: int, patient_data: Dict[str, Any]) -> bool:
        """Update patient demographics"""
        query = """
            UPDATE patients 
            SET first_name = %s, last_name = %s, date_of_birth = %s, gender = %s, 
                phone = %s, email = %s, address = %s, emergency_contact = %s, 
                insurance = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('date_of_birth'),
            patient_data.get('gender'),
            patient_data.get('phone'),
            patient_data.get('email'),
            patient_data.get('address'),
            patient_data.get('emergency_contact'),
            patient_data.get('insurance'),
            patient_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated patient {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update patient {patient_id}: {e}")
            raise DatabaseError("Failed to update patient record")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search patients by name"""
        search_query = """
            SELECT id, first_name, last_name, date_of_birth, gender 
            FROM patients 
            WHERE LOWER(first_name) LIKE %s OR LOWER(last_name) LIKE %s
            ORDER BY last_name, first_name
        """
        
        search_term = f"%{query.lower()}%"
        try:
            return db.execute_query(search_query, (search_term, search_term))
        except Exception as e:
            logger.error(f"Failed to search patients: {e}")
            raise DatabaseError("Failed to search patients")
    
    def get_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        query = "SELECT * FROM patients WHERE id = %s"
        try:
            results = db.execute_query(query, (patient_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get patient {patient_id}: {e}")
            raise DatabaseError("Failed to retrieve patient")

class MedicationService(BaseService):
    """Service for medication operations"""
    
    def __init__(self):
        super().__init__("medications")
    
    def create(self, patient_id: int, medication_data: Dict[str, Any]) -> int:
        """Create a new medication record"""
        query = """
            INSERT INTO medications (patient_id, name, dosage, frequency, start_date, 
                                   end_date, prescribing_doctor, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            medication_data.get('name'),
            medication_data.get('dosage'),
            medication_data.get('frequency'),
            medication_data.get('start_date'),
            medication_data.get('end_date'),
            medication_data.get('prescribing_doctor'),
            medication_data.get('status', 'Active')
        )
        
        try:
            result = db.execute_query(query, params)
            medication_id = result[0]['id']
            logger.info(f"Created medication record with ID {medication_id}")
            return medication_id
        except Exception as e:
            logger.error(f"Failed to create medication: {e}")
            raise DatabaseError("Failed to create medication record")
    
    def update(self, medication_id: int, medication_data: Dict[str, Any]) -> bool:
        """Update medication record"""
        query = """
            UPDATE medications 
            SET name = %s, dosage = %s, frequency = %s, start_date = %s, 
                end_date = %s, prescribing_doctor = %s, status = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            medication_data.get('name'),
            medication_data.get('dosage'),
            medication_data.get('frequency'),
            medication_data.get('start_date'),
            medication_data.get('end_date'),
            medication_data.get('prescribing_doctor'),
            medication_data.get('status'),
            medication_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated medication {medication_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update medication {medication_id}: {e}")
            raise DatabaseError("Failed to update medication record")

class ConditionService(BaseService):
    """Service for medical condition operations"""
    
    def __init__(self):
        super().__init__("conditions")
    
    def create(self, patient_id: int, condition_data: Dict[str, Any]) -> int:
        """Create a new condition record"""
        query = """
            INSERT INTO conditions (patient_id, name, icd_code, status, date_diagnosed, severity)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            condition_data.get('name'),
            condition_data.get('icd_code'),
            condition_data.get('status', 'Active'),
            condition_data.get('date_diagnosed'),
            condition_data.get('severity')
        )
        
        try:
            result = db.execute_query(query, params)
            condition_id = result[0]['id']
            logger.info(f"Created condition record with ID {condition_id}")
            return condition_id
        except Exception as e:
            logger.error(f"Failed to create condition: {e}")
            raise DatabaseError("Failed to create condition record")
    
    def update(self, condition_id: int, condition_data: Dict[str, Any]) -> bool:
        """Update condition record"""
        query = """
            UPDATE conditions 
            SET name = %s, icd_code = %s, status = %s, date_diagnosed = %s, 
                severity = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            condition_data.get('name'),
            condition_data.get('icd_code'),
            condition_data.get('status'),
            condition_data.get('date_diagnosed'),
            condition_data.get('severity'),
            condition_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated condition {condition_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update condition {condition_id}: {e}")
            raise DatabaseError("Failed to update condition record")

class DiagnosisService(BaseService):
    """Service for diagnosis operations"""
    
    def __init__(self):
        super().__init__("diagnoses")
    
    def create(self, patient_id: int, diagnosis_data: Dict[str, Any]) -> int:
        """Create a new diagnosis record"""
        query = """
            INSERT INTO diagnoses (patient_id, date, primary_diagnosis, secondary_diagnosis, 
                                 provider, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            diagnosis_data.get('date'),
            diagnosis_data.get('primary_diagnosis'),
            diagnosis_data.get('secondary_diagnosis'),
            diagnosis_data.get('provider'),
            diagnosis_data.get('notes')
        )
        
        try:
            result = db.execute_query(query, params)
            diagnosis_id = result[0]['id']
            logger.info(f"Created diagnosis record with ID {diagnosis_id}")
            return diagnosis_id
        except Exception as e:
            logger.error(f"Failed to create diagnosis: {e}")
            raise DatabaseError("Failed to create diagnosis record")
    
    def update(self, diagnosis_id: int, diagnosis_data: Dict[str, Any]) -> bool:
        """Update diagnosis record"""
        query = """
            UPDATE diagnoses 
            SET date = %s, primary_diagnosis = %s, secondary_diagnosis = %s, 
                provider = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            diagnosis_data.get('date'),
            diagnosis_data.get('primary_diagnosis'),
            diagnosis_data.get('secondary_diagnosis'),
            diagnosis_data.get('provider'),
            diagnosis_data.get('notes'),
            diagnosis_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated diagnosis {diagnosis_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update diagnosis {diagnosis_id}: {e}")
            raise DatabaseError("Failed to update diagnosis record")

class ClinicalNoteService(BaseService):
    """Service for clinical note operations"""
    
    def __init__(self):
        super().__init__("clinical_notes")
    
    def create(self, patient_id: int, note_data: Dict[str, Any]) -> int:
        """Create a new clinical note record"""
        query = """
            INSERT INTO clinical_notes (patient_id, date, provider, type, note)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            note_data.get('date'),
            note_data.get('provider'),
            note_data.get('type'),
            note_data.get('note')
        )
        
        try:
            result = db.execute_query(query, params)
            note_id = result[0]['id']
            logger.info(f"Created clinical note record with ID {note_id}")
            return note_id
        except Exception as e:
            logger.error(f"Failed to create clinical note: {e}")
            raise DatabaseError("Failed to create clinical note record")
    
    def update(self, note_id: int, note_data: Dict[str, Any]) -> bool:
        """Update clinical note record"""
        query = """
            UPDATE clinical_notes 
            SET date = %s, provider = %s, type = %s, note = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            note_data.get('date'),
            note_data.get('provider'),
            note_data.get('type'),
            note_data.get('note'),
            note_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated clinical note {note_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update clinical note {note_id}: {e}")
            raise DatabaseError("Failed to update clinical note record")

class AllergyService(BaseService):
    """Service for allergy operations"""
    
    def __init__(self):
        super().__init__("allergies")
    
    def create(self, patient_id: int, allergy_data: Dict[str, Any]) -> int:
        """Create a new allergy record"""
        query = """
            INSERT INTO allergies (patient_id, allergen, reaction, severity, date_identified)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            allergy_data.get('allergen'),
            allergy_data.get('reaction'),
            allergy_data.get('severity'),
            allergy_data.get('date_identified')
        )
        
        try:
            result = db.execute_query(query, params)
            allergy_id = result[0]['id']
            logger.info(f"Created allergy record with ID {allergy_id}")
            return allergy_id
        except Exception as e:
            logger.error(f"Failed to create allergy: {e}")
            raise DatabaseError("Failed to create allergy record")
    
    def update(self, allergy_id: int, allergy_data: Dict[str, Any]) -> bool:
        """Update allergy record"""
        query = """
            UPDATE allergies 
            SET allergen = %s, reaction = %s, severity = %s, date_identified = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            allergy_data.get('allergen'),
            allergy_data.get('reaction'),
            allergy_data.get('severity'),
            allergy_data.get('date_identified'),
            allergy_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated allergy {allergy_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update allergy {allergy_id}: {e}")
            raise DatabaseError("Failed to update allergy record")

class ImmunizationService(BaseService):
    """Service for immunization operations"""
    
    def __init__(self):
        super().__init__("immunizations")
    
    def create(self, patient_id: int, immunization_data: Dict[str, Any]) -> int:
        """Create a new immunization record"""
        query = """
            INSERT INTO immunizations (patient_id, vaccine, date_administered, provider, lot_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            immunization_data.get('vaccine'),
            immunization_data.get('date_administered'),
            immunization_data.get('provider'),
            immunization_data.get('lot_number')
        )
        
        try:
            result = db.execute_query(query, params)
            immunization_id = result[0]['id']
            logger.info(f"Created immunization record with ID {immunization_id}")
            return immunization_id
        except Exception as e:
            logger.error(f"Failed to create immunization: {e}")
            raise DatabaseError("Failed to create immunization record")
    
    def update(self, immunization_id: int, immunization_data: Dict[str, Any]) -> bool:
        """Update immunization record"""
        query = """
            UPDATE immunizations 
            SET vaccine = %s, date_administered = %s, provider = %s, lot_number = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            immunization_data.get('vaccine'),
            immunization_data.get('date_administered'),
            immunization_data.get('provider'),
            immunization_data.get('lot_number'),
            immunization_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated immunization {immunization_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update immunization {immunization_id}: {e}")
            raise DatabaseError("Failed to update immunization record")

class AppointmentService(BaseService):
    """Service for appointment operations"""
    
    def __init__(self):
        super().__init__("appointments")
    
    def create(self, patient_id: int, appointment_data: Dict[str, Any]) -> int:
        """Create a new appointment record"""
        #pdb.set_trace()
        query = """
            INSERT INTO appointments (patient_id, date, time, provider, type, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            patient_id,
            appointment_data.get('date'),
            appointment_data.get('time'),
            appointment_data.get('provider'),
            appointment_data.get('type'),
            appointment_data.get('status', 'Scheduled'),
            appointment_data.get('notes')
        )
        
        try:
            result = db.execute_query(query, params)
            appointment_id = result[0]['id']
            logger.info(f"Created appointment record with ID {appointment_id}")
            return appointment_id
        except Exception as e:
            logger.error(f"Failed to create appointment: {e}")
            raise DatabaseError("Failed to create appointment record")
    
    def update(self, appointment_id: int, appointment_data: Dict[str, Any]) -> bool:
        """Update appointment record"""
        query = """
            UPDATE appointments 
            SET date = %s, time = %s, provider = %s, type = %s, status = %s, 
                notes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            appointment_data.get('date'),
            appointment_data.get('time'),
            appointment_data.get('provider'),
            appointment_data.get('type'),
            appointment_data.get('status'),
            appointment_data.get('notes'),
            appointment_id
        )
        
        try:
            db.execute_query(query, params, fetch=False)
            logger.info(f"Updated appointment {appointment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update appointment {appointment_id}: {e}")
            raise DatabaseError("Failed to update appointment record")

# Service instances
patient_service = PatientService()
medication_service = MedicationService()
condition_service = ConditionService()
diagnosis_service = DiagnosisService()
clinical_note_service = ClinicalNoteService()
allergy_service = AllergyService()
immunization_service = ImmunizationService()
appointment_service = AppointmentService()
