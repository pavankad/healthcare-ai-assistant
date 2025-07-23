#!/usr/bin/env python3
"""
Web-based Audio Transcriber Integration
Connects the audio transcriber with the EMR system via web APIs
"""

import threading
import time
import requests
import json
import logging
from audio_transcriber import AudioTranscriber

logger = logging.getLogger(__name__)

class WebAudioTranscriber:
    def __init__(self, emr_base_url="http://localhost:5000"):
        self.emr_base_url = emr_base_url
        self.session = requests.Session()
        self.current_note_id = None
        self.transcriber = None
        self.is_authenticated = False
        
    def login(self, username="admin", password="admin"):
        """Login to the EMR system"""
        try:
            login_data = {"username": username, "password": password}
            response = self.session.post(f"{self.emr_base_url}/login", data=login_data)
            
            if response.status_code == 200:
                self.is_authenticated = True
                logger.info("Successfully logged into EMR system")
                return True
            else:
                logger.error(f"EMR login failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error logging into EMR: {e}")
            return False
    
    def start_recording_session(self, patient_id, provider="Voice Transcription"):
        """Start a new recording session"""
        if not self.is_authenticated:
            if not self.login():
                return None
        
        try:
            data = {
                "patient_id": patient_id,
                "provider": provider
            }
            
            response = self.session.post(
                f"{self.emr_base_url}/api/voice/start-recording",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.current_note_id = result.get('note_id')
                logger.info(f"Started recording session with note ID: {self.current_note_id}")
                return self.current_note_id
            else:
                logger.error(f"Failed to start recording session: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting recording session: {e}")
            return None
    
    def stop_recording_session(self):
        """Stop the current recording session"""
        if not self.current_note_id:
            return True
        
        try:
            data = {"note_id": self.current_note_id}
            
            response = self.session.post(
                f"{self.emr_base_url}/api/voice/stop-recording",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 200
            if success:
                logger.info(f"Stopped recording session for note ID: {self.current_note_id}")
                self.current_note_id = None
            else:
                logger.error(f"Failed to stop recording session: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error stopping recording session: {e}")
            return False
    
    def add_transcription(self, transcription):
        """Add transcribed text to the current session"""
        if not self.current_note_id or not transcription.strip():
            return False
        
        try:
            data = {
                "note_id": self.current_note_id,
                "transcription": transcription.strip()
            }
            
            response = self.session.post(
                f"{self.emr_base_url}/api/voice/add-transcription",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 200
            if success:
                logger.info(f"Added transcription: {transcription[:50]}...")
            else:
                logger.error(f"Failed to add transcription: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding transcription: {e}")
            return False
    
    def start_audio_recording(self, patient_id, model_size="base", chunk_duration=30):
        """Start audio recording with transcription"""
        # Start the recording session
        note_id = self.start_recording_session(patient_id)
        if not note_id:
            return False
        
        # Create transcriber with callback
        def on_transcription(text):
            self.add_transcription(text)
        
        self.transcriber = AudioTranscriber(
            model_size=model_size,
            chunk_duration=chunk_duration,
            on_transcription=on_transcription
        )
        
        # Start recording
        self.transcriber.start_recording()
        return True
    
    def stop_audio_recording(self):
        """Stop audio recording"""
        success = True
        
        # Stop the transcriber
        if self.transcriber:
            self.transcriber.stop_recording()
            self.transcriber = None
        
        # Stop the recording session
        if not self.stop_recording_session():
            success = False
        
        return success

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web-based Audio Transcriber")
    parser.add_argument("--patient-id", type=int, required=True, help="Patient ID")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large"], 
                       default="base", help="Whisper model size")
    parser.add_argument("--duration", type=int, default=30, help="Audio chunk duration")
    parser.add_argument("--emr-url", type=str, default="http://localhost:5000", 
                       help="EMR system URL")
    
    args = parser.parse_args()
    
    # Create web transcriber
    transcriber = WebAudioTranscriber(args.emr_url)
    
    try:
        print(f"🏥 Starting voice recording for patient {args.patient_id}")
        
        if transcriber.start_audio_recording(args.patient_id, args.model, args.duration):
            print("🎤 Recording started. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while True:
                time.sleep(1)
        else:
            print("❌ Failed to start recording")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping recording...")
        transcriber.stop_audio_recording()
        print("📋 Recording session completed")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        transcriber.stop_audio_recording()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
