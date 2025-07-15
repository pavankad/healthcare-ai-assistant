"""
PostgreSQL database connection and operations for EMR system
Implements secure connection pooling and CRUD operations
"""

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Union
import json
from datetime import datetime, date, time
from config import db_config

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class EMRDatabase:
    """
    PostgreSQL database manager for EMR system with connection pooling
    Implements secure database operations with proper error handling
    """
    
    def __init__(self):
        """Initialize database connection pool"""
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize PostgreSQL connection pool with retry logic"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=db_config.pool_size,
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                password=db_config.password,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic cleanup
        Ensures proper resource management and error handling
        """
        connection = None
        try:
            connection = self.connection_pool.getconn()
            if connection:
                yield connection
            else:
                raise DatabaseError("Failed to get database connection from pool")
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """
        Execute SQL query with parameterized inputs for security
        Args:
            query: SQL query string
            params: Query parameters (prevents SQL injection)
            fetch: Whether to fetch results
        Returns:
            Query results or None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, params)
                    conn.commit()
                    
                    if fetch:
                        results = cursor.fetchall()
                        # Convert RealDictRow to regular dict for JSON serialization
                        return [dict(row) for row in results] if results else []
                    return None
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Query execution failed: {e}")
                    raise DatabaseError(f"Query failed: {e}")
    
    def create_tables(self):
        """Create all necessary tables for EMR system"""
        tables = {
            'patients': '''
                CREATE TABLE IF NOT EXISTS patients (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    date_of_birth DATE NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    address TEXT,
                    emergency_contact TEXT,
                    insurance TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'medications': '''
                CREATE TABLE IF NOT EXISTS medications (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    dosage VARCHAR(100) NOT NULL,
                    frequency VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    prescribing_doctor VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'conditions': '''
                CREATE TABLE IF NOT EXISTS conditions (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    icd_code VARCHAR(20),
                    status VARCHAR(50) DEFAULT 'Active',
                    date_diagnosed DATE NOT NULL,
                    severity VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'diagnoses': '''
                CREATE TABLE IF NOT EXISTS diagnoses (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    primary_diagnosis VARCHAR(200) NOT NULL,
                    secondary_diagnosis VARCHAR(200),
                    provider VARCHAR(100) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'clinical_notes': '''
                CREATE TABLE IF NOT EXISTS clinical_notes (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    note TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'allergies': '''
                CREATE TABLE IF NOT EXISTS allergies (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    allergen VARCHAR(200) NOT NULL,
                    reaction TEXT NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    date_identified DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'immunizations': '''
                CREATE TABLE IF NOT EXISTS immunizations (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    vaccine VARCHAR(200) NOT NULL,
                    date_administered DATE NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    lot_number VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'appointments': '''
                CREATE TABLE IF NOT EXISTS appointments (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'Scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        # Create tables with proper error handling
        for table_name, create_sql in tables.items():
            try:
                self.execute_query(create_sql, fetch=False)
                logger.info(f"Table '{table_name}' created/verified successfully")
            except Exception as e:
                logger.error(f"Failed to create table '{table_name}': {e}")
                raise DatabaseError(f"Table creation failed for {table_name}: {e}")
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_conditions_patient ON conditions(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient ON clinical_notes(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_allergies_patient ON allergies(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_immunizations_patient ON immunizations(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)"
        ]
        
        for index_sql in indexes:
            try:
                self.execute_query(index_sql, fetch=False)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    def insert_sample_data(self):
        """Insert sample data for testing purposes"""
        # Insert sample patients
        patients_data = [
            ('John', 'Doe', '1985-03-15', 'Male', '(555) 123-4567', 'john.doe@email.com', 
             '123 Main St, City, State 12345', 'Jane Doe - (555) 987-6543', 
             'BlueCross BlueShield - Policy #BC123456'),
            ('Jane', 'Smith', '1978-08-22', 'Female', '(555) 234-5678', 'jane.smith@email.com',
             '456 Oak Ave, City, State 12345', 'Bob Smith - (555) 876-5432',
             'Aetna - Policy #AE789012')
        ]
        
        for patient_data in patients_data:
            try:
                # Check if patient already exists
                existing = self.execute_query(
                    "SELECT id FROM patients WHERE first_name = %s AND last_name = %s AND date_of_birth = %s",
                    (patient_data[0], patient_data[1], patient_data[2])
                )
                
                if not existing:
                    self.execute_query(
                        """INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, 
                           address, emergency_contact, insurance) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        patient_data,
                        fetch=False
                    )
                    logger.info(f"Sample patient {patient_data[0]} {patient_data[1]} inserted")
            except Exception as e:
                logger.warning(f"Failed to insert sample patient: {e}")
    
    def close(self):
        """Close all database connections"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database instance
db = EMRDatabase()

def json_serializer(obj):
    """JSON serializer for datetime, date, and time objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def initialize_database():
    """Initialize database tables and sample data"""
    try:
        db.create_tables()
        db.insert_sample_data()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    # Initialize database when run directly
    initialize_database()
