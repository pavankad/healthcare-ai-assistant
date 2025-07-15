#!/usr/bin/env python3
"""
Audio Transcriber using OpenAI Whisper
Captures audio chunks and converts them to text using Whisper model.
Useful for adding voice notes to clinical records.
"""

import pyaudio
import wave
import threading
import time
import os
import tempfile
from datetime import datetime
import argparse
import whisper
import numpy as np
from typing import Optional, Callable
import logging
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, 
                 model_size: str = "base",
                 chunk_duration: int = 30,
                 sample_rate: int = 16000,
                 channels: int = 1,
                 format: int = pyaudio.paInt16,
                 on_transcription: Optional[Callable[[str], None]] = None,
                 patient_id: Optional[int] = None,
                 provider_name: str = "Voice Transcription",
                 emr_base_url: str = "http://localhost:5000"):
        """
        Initialize the AudioTranscriber
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            chunk_duration: Duration of each audio chunk in seconds
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
            format: Audio format (pyaudio format)
            on_transcription: Callback function called when transcription is available
            patient_id: EMR patient ID to create/update clinical notes
            provider_name: Name of the provider for clinical notes
            emr_base_url: Base URL of the EMR system
        """
        self.model_size = model_size
        self.chunk_duration = chunk_duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.on_transcription = on_transcription
        
        # EMR integration parameters
        self.patient_id = patient_id
        self.provider_name = provider_name
        self.emr_base_url = emr_base_url
        self.current_note_id = None
        self.session = requests.Session()
        self.accumulated_text = ""
        
        # Audio recording parameters
        self.chunk_size = 1024
        self.frames_per_chunk = int(sample_rate * chunk_duration)
        
        # State variables
        self.is_recording = False
        self.audio_buffer = []
        self.recording_thread = None
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Load Whisper model
        logger.info(f"Loading Whisper model: {model_size}")
        self.whisper_model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully")
        
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    def login_to_emr(self, username: str = "admin", password: str = "admin") -> bool:
        """Login to the EMR system"""
        try:
            login_data = {"username": username, "password": password}
            response = self.session.post(f"{self.emr_base_url}/login", data=login_data)
            
            if response.status_code == 200:
                logger.info("Successfully logged into EMR system")
                print("🔐 Successfully logged into EMR system")
                return True
            else:
                logger.error(f"EMR login failed: {response.status_code}")
                print(f"❌ EMR login failed with status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error logging into EMR: {e}")
            print(f"❌ Error logging into EMR: {e}")
            return False
    

    def create_clinical_note(self) -> bool:
        """Create a new clinical note for the current session"""
        if not self.patient_id:
            logger.warning("No patient ID provided, cannot create clinical note")
            return False
        
        try:
            note_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "provider": self.provider_name,
                "type": "Voice Transcription",
                "note": "🎤 Voice transcription started - content will be updated in real-time...\n\n"
            }
            
            response = self.session.post(
                f"{self.emr_base_url}/api/patients/{self.patient_id}/clinical-notes",
                json=note_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.current_note_id = result.get('note_id')
                self.accumulated_text = note_data["note"]
                logger.info(f"Created clinical note with ID: {self.current_note_id}")
                print(f"📝 Created clinical note ID {self.current_note_id} for patient {self.patient_id}")
                return True
            else:
                logger.error(f"Failed to create clinical note: {response.status_code}")
                print(f"❌ Failed to create clinical note: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating clinical note: {e}")
            print(f"❌ Error creating clinical note: {e}")
            return False
    
    def update_clinical_note(self, new_text: str):
        """Update the current clinical note with new transcribed text"""
        if not self.current_note_id:
            logger.warning("No current note ID, cannot update clinical note")
            return
        
        try:
            # Add timestamp and new text
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] {new_text}\n"
            self.accumulated_text += formatted_text
            
            # Update the note
            update_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "provider": self.provider_name,
                "type": "Voice Transcription",
                "note": self.accumulated_text
            }
            
            response = self.session.put(
                f"{self.emr_base_url}/api/clinical-notes/{self.current_note_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("Clinical note updated successfully")
                print(f"✅ Updated clinical note: {new_text[:50]}...")
            else:
                logger.error(f"Failed to update clinical note: {response.status_code}")
                print(f"❌ Failed to update clinical note: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error updating clinical note: {e}")
            print(f"❌ Error updating clinical note: {e}")
    
    def finalize_clinical_note(self):
        """Finalize the clinical note when recording stops"""
        if not self.current_note_id:
            return
        
        try:
            # Add completion timestamp
            completion_text = f"\n🛑 Voice transcription completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.accumulated_text += completion_text
            
            update_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "provider": self.provider_name,
                "type": "Voice Transcription",
                "note": self.accumulated_text
            }
            
            response = self.session.put(
                f"{self.emr_base_url}/api/clinical-notes/{self.current_note_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("Clinical note finalized")
                print(f"🏁 Clinical note ID {self.current_note_id} finalized")
            else:
                logger.error(f"Failed to finalize clinical note: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error finalizing clinical note: {e}")
        finally:
            self.current_note_id = None
            self.accumulated_text = ""
    
    def start_recording(self):
        """Start continuous audio recording and transcription"""
        if self.is_recording:
            logger.warning("Recording is already in progress")
            return
        
        # Login to EMR and create clinical note if patient ID is provided
        if self.patient_id:
            print(f"🏥 Connecting to EMR system for patient {self.patient_id}...")
            if self.login_to_emr():
                if self.create_clinical_note():
                    print("📝 Clinical note created - transcriptions will be written in real-time")
                else:
                    print("⚠️ Failed to create clinical note, continuing with audio-only mode")
            else:
                print("⚠️ Failed to connect to EMR, continuing with audio-only mode")
        
        self.is_recording = True
        self.audio_buffer = []
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logger.info("Audio recording started")
        print(f"🎤 Recording started - {self.chunk_duration}s chunks, {self.model_size} model")
        if self.patient_id:
            print("💡 Speak clearly - your words will appear in the clinical note in real-time!")
        print("Press Ctrl+C to stop recording")
            
        self.is_recording = True
        self.audio_buffer = []
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logger.info("Audio recording started")
        print(f"🎤 Recording started - {self.chunk_duration}s chunks, {self.model_size} model")
        if self.patient_id:
            print("💡 Speak clearly - your words will appear in the clinical note in real-time!")
        print("Press Ctrl+C to stop recording")
    
    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            logger.warning("Recording is not in progress")
            return
            
        self.is_recording = False
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # Finalize clinical note if one was created
        if self.current_note_id:
            self.finalize_clinical_note()
            
        logger.info("Audio recording stopped")
        print("🛑 Recording stopped")
        if self.patient_id:
            print("📋 Clinical note has been finalized")
    
    def _recording_loop(self):
        """Main recording loop that runs in a separate thread"""
        try:
            # Open audio stream
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Audio stream opened")
            
            while self.is_recording:
                # Record audio chunk
                frames = []
                for _ in range(0, self.frames_per_chunk, self.chunk_size):
                    if not self.is_recording:
                        break
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                
                if frames and self.is_recording:
                    # Process the recorded chunk
                    audio_data = b''.join(frames)
                    self._process_audio_chunk(audio_data)
            
            # Close audio stream
            stream.stop_stream()
            stream.close()
            logger.info("Audio stream closed")
            
        except Exception as e:
            logger.error(f"Error in recording loop: {e}")
            self.is_recording = False
    
    def _process_audio_chunk(self, audio_data: bytes):
        """Process a single audio chunk and transcribe it"""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Write WAV file
                with wave.open(temp_filename, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)
            
            # Transcribe using Whisper
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"🔄 [{timestamp}] Processing audio chunk...")
            
            result = self.whisper_model.transcribe(temp_filename)
            transcription = result['text'].strip()
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            if transcription:
                print(f"📝 [{timestamp}] Transcription: {transcription}")
                
                # Update clinical note if available
                if self.current_note_id:
                    self.update_clinical_note(transcription)
                
                # Call callback if provided
                if self.on_transcription:
                    self.on_transcription(transcription)
            else:
                print(f"🔇 [{timestamp}] No speech detected")
                
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    def transcribe_file(self, audio_file_path: str) -> str:
        """Transcribe an existing audio file"""
        try:
            logger.info(f"Transcribing file: {audio_file_path}")
            result = self.whisper_model.transcribe(audio_file_path)
            transcription = result['text'].strip()
            logger.info("File transcription completed")
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return ""

def save_transcription_to_file(transcription: str, filename: str = None):
    """Save transcription to a text file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{timestamp}.txt"
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {transcription}\n")
        logger.info(f"Transcription saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving transcription: {e}")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Audio Transcriber using OpenAI Whisper")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large"], 
                       default="base", help="Whisper model size")
    parser.add_argument("--duration", type=int, default=30, 
                       help="Audio chunk duration in seconds")
    parser.add_argument("--file", type=str, help="Transcribe an existing audio file")
    parser.add_argument("--output", type=str, help="Output file for transcriptions")
    parser.add_argument("--sample-rate", type=int, default=16000, 
                       help="Audio sample rate in Hz")
    parser.add_argument("--patient-id", type=int, 
                       help="EMR Patient ID to create/update clinical notes")
    parser.add_argument("--provider", type=str, default="Voice Transcription",
                       help="Provider name for clinical notes")
    parser.add_argument("--emr-url", type=str, default="http://localhost:5000",
                       help="EMR system base URL")
    
    args = parser.parse_args()
    
    # Define transcription callback
    def on_transcription_callback(text: str):
        if args.output:
            save_transcription_to_file(text, args.output)
    
    # Create transcriber
    transcriber = AudioTranscriber(
        model_size=args.model,
        chunk_duration=args.duration,
        sample_rate=args.sample_rate,
        on_transcription=on_transcription_callback,
        patient_id=args.patient_id,
        provider_name=args.provider,
        emr_base_url=args.emr_url
    )
    
    if args.file:
        # Transcribe existing file
        print(f"🎵 Transcribing file: {args.file}")
        transcription = transcriber.transcribe_file(args.file)
        if transcription:
            print(f"📝 Transcription: {transcription}")
            if args.output:
                save_transcription_to_file(transcription, args.output)
        else:
            print("❌ No transcription generated")
    else:
        # Start live recording
        try:
            transcriber.start_recording()
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping transcription...")
            transcriber.stop_recording()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            transcriber.stop_recording()

if __name__ == "__main__":
    main()
