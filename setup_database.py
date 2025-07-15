#!/usr/bin/env python3
"""
Database setup script for EMR system
Creates PostgreSQL database and tables, inserts sample data
"""

import sys
import os
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from config import db_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_postgresql():
    """Check if PostgreSQL is installed and running"""
    try:
        result = subprocess.run(['pg_isready'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def create_database():
    """Create the EMR database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config.database,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {db_config.database}")
            logger.info(f"Database '{db_config.database}' created successfully")
        else:
            logger.info(f"Database '{db_config.database}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False

def create_user():
    """Create database user if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            user='postgres',  # Use postgres superuser
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = %s", (db_config.username,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"""
                CREATE USER {db_config.username} 
                WITH PASSWORD '{db_config.password}'
            """)
            logger.info(f"User '{db_config.username}' created successfully")
        else:
            logger.info(f"User '{db_config.username}' already exists")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_config.database} TO {db_config.username}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return False

def setup_database():
    """Set up the complete database"""
    logger.info("Starting database setup...")
    
    # Check PostgreSQL availability
    if not check_postgresql():
        logger.error("PostgreSQL is not running or not installed")
        logger.info("Please install PostgreSQL and ensure it's running")
        logger.info("On macOS: brew install postgresql && brew services start postgresql")
        logger.info("On Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        return False
    
    # Create database and user
    if not create_database():
        return False
    
    # Initialize tables and data
    try:
        from database import initialize_database
        initialize_database()
        logger.info("Database setup completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def reset_database():
    """Reset the database (drop and recreate)"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Terminate existing connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_config.database}'
            AND pid <> pg_backend_pid()
        """)
        
        # Drop and recreate database
        cursor.execute(f"DROP DATABASE IF EXISTS {db_config.database}")
        cursor.execute(f"CREATE DATABASE {db_config.database}")
        
        cursor.close()
        conn.close()
        
        logger.info(f"Database '{db_config.database}' reset successfully")
        
        # Initialize tables and data
        from database import initialize_database
        initialize_database()
        logger.info("Database reset and reinitialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        success = reset_database()
    else:
        success = setup_database()
    
    if success:
        logger.info("Database is ready for use!")
        logger.info(f"Connection details:")
        logger.info(f"  Host: {db_config.host}")
        logger.info(f"  Port: {db_config.port}")
        logger.info(f"  Database: {db_config.database}")
        logger.info(f"  Username: {db_config.username}")
    else:
        logger.error("Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
