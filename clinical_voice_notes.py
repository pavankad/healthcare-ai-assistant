#!/usr/bin/env python3
"""
Clinical Voice Notes Example
Demonstrates real-time voice transcription to EMR clinical notes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_transcriber import AudioTranscriber
import time

def main():
    print("🏥 Clinical Voice Notes - EMR Integration Demo")
    print("=" * 50)
    
    # Configuration
    patient_id = input("Enter Patient ID (or press Enter for Patient ID 1): ").strip()
    if not patient_id:
        patient_id = 1
    else:
        try:
            patient_id = int(patient_id)
        except ValueError:
            print("❌ Invalid Patient ID, using Patient ID 1")
            patient_id = 1
    
    provider_name = input("Enter Provider Name (or press Enter for 'Dr. Voice Assistant'): ").strip()
    if not provider_name:
        provider_name = "Dr. Voice Assistant"
    
    print(f"\n🎯 Configuration:")
    print(f"   Patient ID: {patient_id}")
    print(f"   Provider: {provider_name}")
    print(f"   EMR URL: http://localhost:5000")
    print()
    
    # Create transcriber with EMR integration
    transcriber = AudioTranscriber(
        model_size="base",  # Good balance of speed and accuracy
        chunk_duration=10,  # Shorter chunks for more responsive updates
        patient_id=patient_id,
        provider_name=provider_name,
        emr_base_url="http://localhost:5000"
    )
    
    print("💡 Instructions:")
    print("   1. Make sure the EMR system is running (python app.py)")
    print("   2. Open EMR UI in browser: http://localhost:5000")
    print("   3. Login with admin/admin")
    print("   4. Select the patient and go to Clinical Notes tab")
    print("   5. Start speaking - your words will appear in real-time!")
    print("   6. Press Ctrl+C to stop recording")
    print()
    
    input("Press Enter to start recording...")
    
    try:
        transcriber.start_recording()
        print("\n🎤 Recording started! Speak clearly into your microphone...")
        print("📝 Watch the EMR Clinical Notes tab for real-time updates!")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping recording...")
        transcriber.stop_recording()
        print("✅ Recording session completed!")
        print("📋 Check the EMR system for the final clinical note.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        transcriber.stop_recording()

if __name__ == "__main__":
    main()
