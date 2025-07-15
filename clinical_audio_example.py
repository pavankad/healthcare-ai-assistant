#!/usr/bin/env python3
"""
Example usage of the AudioTranscriber for clinical notes
This script demonstrates how to integrate voice transcription with the EMR system
"""

import sys
import os
import requests
import json
from datetime import datetime
from audio_transcriber import AudioTranscriber

class ClinicalAudioRecorder:
    def __init__(self, patient_id: int, provider_name: str, emr_base_url: str = "http://localhost:5000"):
        """
        Initialize clinical audio recorder
        
        Args:
            patient_id: ID of the patient for clinical notes
            provider_name: Name of the healthcare provider
            emr_base_url: Base URL of the EMR system
        """
        self.patient_id = patient_id
        self.provider_name = provider_name
        self.emr_base_url = emr_base_url
        self.session = requests.Session()
        
        # Initialize transcriber with callback
        self.transcriber = AudioTranscriber(
            model_size="base",
            chunk_duration=1,  # Shorter chunks for more responsive feedback
            on_transcription=self.on_transcription_received
        )
        
        self.accumulated_text = []
        
    def on_transcription_received(self, transcription: str):
        """Handle new transcription text"""
        if transcription.strip():
            print(f"🎤 Transcribed: {transcription}")
            self.accumulated_text.append(transcription.strip())
            
            # Auto-save if we have enough content (optional)
            if len(' '.join(self.accumulated_text)) > 200:  # Save after ~200 characters
                self.save_clinical_note()
    
    def save_clinical_note(self, note_type: str = "Progress Note", force_save: bool = False):
        """Save accumulated transcriptions as a clinical note"""
        if not self.accumulated_text and not force_save:
            print("❌ No transcription text to save")
            return False
            
        # Combine all transcribed text
        full_note = ' '.join(self.accumulated_text)
        
        # Prepare clinical note data
        note_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "provider": self.provider_name,
            "type": note_type,
            "note": full_note
        }
        
        try:
            # Send to EMR system
            url = f"{self.emr_base_url}/api/patients/{self.patient_id}/clinical-notes"
            response = self.session.post(url, json=note_data)
            
            if response.status_code == 201:
                print(f"✅ Clinical note saved successfully!")
                print(f"📝 Note: {full_note[:100]}{'...' if len(full_note) > 100 else ''}")
                
                # Clear accumulated text after successful save
                self.accumulated_text = []
                return True
            else:
                print(f"❌ Failed to save clinical note: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving clinical note: {e}")
            return False
    
    def start_recording(self):
        """Start voice recording for clinical notes"""
        print(f"🏥 Starting clinical voice recording for Patient ID: {self.patient_id}")
        print(f"👩‍⚕️ Provider: {self.provider_name}")
        print("🎤 Speak your clinical notes. Press Ctrl+C when finished.")
        print("-" * 60)
        
        try:
            self.transcriber.start_recording()
            
            # Keep running until interrupted
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping recording...")
            self.transcriber.stop_recording()
            
            # Save any remaining transcriptions
            if self.accumulated_text:
                print("💾 Saving final clinical note...")
                self.save_clinical_note(force_save=True)
            else:
                print("ℹ️  No transcriptions to save")
        
        except Exception as e:
            print(f"❌ Error during recording: {e}")
            self.transcriber.stop_recording()

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python clinical_audio_example.py <patient_id> <provider_name> [emr_url]")
        print("Example: python clinical_audio_example.py 1 'Dr. Smith' 'http://localhost:5000'")
        sys.exit(1)
    
    patient_id = int(sys.argv[1])
    provider_name = sys.argv[2]
    emr_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:5000"
    
    # Create clinical audio recorder
    recorder = ClinicalAudioRecorder(patient_id, provider_name, emr_url)
    
    # Start recording
    recorder.start_recording()

if __name__ == "__main__":
    main()
