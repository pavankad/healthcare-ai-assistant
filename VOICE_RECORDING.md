# Voice Recording Feature

## Overview
The voice recording feature allows healthcare providers to create clinical notes by speaking directly into their microphone. The audio is transcribed in real-time using OpenAI's Whisper model and automatically added to the patient's clinical notes.

## Setup Requirements

### 1. Install Audio Dependencies
```bash
pip install pyaudio whisper soundfile
```

### 2. Additional System Dependencies

**macOS:**
```bash
brew install portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Windows:**
PyAudio should install automatically with pip.

### 3. Microphone Permissions
Make sure your browser has microphone permissions enabled for the EMR application.

## How to Use

### Web Interface (Dashboard)

1. **Select a Patient**: Choose a patient from the patient search
2. **Start Recording**: Click the microphone button in the Medical Information section
3. **Grant Permissions**: Allow microphone access when prompted by your browser
4. **Speak Clearly**: Your speech will be transcribed in real-time
5. **Stop Recording**: Click the microphone button again to stop
6. **View Results**: The transcription appears as a clinical note in the patient's record

### Command Line Interface

You can also use the voice recording from the command line:

```bash
# Basic usage
python web_audio_transcriber.py --patient-id 1

# With custom model and settings
python web_audio_transcriber.py --patient-id 1 --model base --duration 30

# With custom EMR URL
python web_audio_transcriber.py --patient-id 1 --emr-url http://localhost:5000
```

### Standalone Audio Transcriber

For offline transcription or integration with other systems:

```bash
# Real-time transcription
python audio_transcriber.py --model base --duration 30

# Transcribe existing audio file
python audio_transcriber.py --file audio.wav --output transcription.txt

# With EMR integration
python audio_transcriber.py --patient-id 1 --provider "Dr. Smith"
```

## Features

### Real-time Transcription
- Audio is processed in chunks (default 30 seconds)
- Transcriptions appear in clinical notes as they are generated
- Timestamps are added to each transcription segment

### Multiple Model Sizes
Choose the Whisper model based on your needs:
- `tiny`: Fastest, least accurate
- `base`: Good balance of speed and accuracy (default)
- `small`: Better accuracy, slower
- `medium`: High accuracy, requires more memory
- `large`: Best accuracy, slowest

### Clinical Note Integration
- Automatically creates a new clinical note for each recording session
- Updates the note in real-time as transcriptions are generated
- Adds timestamps and completion markers
- Preserves all transcribed content

## Configuration Options

### Audio Settings
```python
model_size = "base"        # Whisper model size
chunk_duration = 30        # Seconds per audio chunk
sample_rate = 16000        # Audio sample rate (Hz)
channels = 1               # Mono audio
```

### Web Interface Settings
```javascript
// Automatic refresh of clinical notes
pollingInterval = 500      // Milliseconds between updates

// Recording status indicators
recordingStatus = true     // Show recording indicator
micButtonToggle = true     // Enable microphone button
```

## Troubleshooting

### Common Issues

**Microphone not working:**
- Check browser permissions
- Ensure microphone is not used by another application
- Try refreshing the page

**Audio quality issues:**
- Speak clearly and close to the microphone
- Reduce background noise
- Use a headset microphone for better quality

**Transcription errors:**
- Try a larger Whisper model (small, medium, large)
- Increase chunk duration for longer phrases
- Speak more slowly and clearly

**Performance issues:**
- Use smaller model (tiny, base) for faster processing
- Reduce chunk duration for more frequent updates
- Ensure adequate system memory for larger models

### Log Files
Check the application logs for detailed error information:
```bash
# Flask application logs
tail -f app.log

# Audio transcriber logs
python audio_transcriber.py --verbose
```

## API Endpoints

### Start Recording
```http
POST /api/voice/start-recording
Content-Type: application/json

{
    "patient_id": 1,
    "provider": "Dr. Smith"
}
```

### Stop Recording
```http
POST /api/voice/stop-recording
Content-Type: application/json

{
    "note_id": "12345"
}
```

### Add Transcription
```http
POST /api/voice/add-transcription
Content-Type: application/json

{
    "note_id": "12345",
    "transcription": "Patient reports feeling better today..."
}
```

### Real-time Updates
```http
GET /api/voice/transcription-stream/<note_id>
Accept: text/event-stream
```

## Security Considerations

- Voice recordings are processed locally using Whisper
- No audio data is sent to external services
- Clinical notes are stored securely in the EMR database
- Session management ensures data privacy between patients

## Integration with EMR

The voice recording feature integrates seamlessly with the existing EMR system:

- **Patient Context**: Recordings are automatically associated with the selected patient
- **Clinical Notes**: Transcriptions become standard clinical notes
- **Provider Attribution**: Notes are attributed to the logged-in provider
- **Real-time Updates**: Other users see transcriptions as they are generated
- **Edit Capability**: Generated notes can be edited like any other clinical note

## Future Enhancements

- **Speaker Recognition**: Identify different speakers in group settings
- **Medical Terminology**: Specialized models trained on medical vocabulary
- **Voice Commands**: Control EMR functions through voice commands
- **Dictation Templates**: Pre-defined templates for common note types
- **Audio Archival**: Optional storage of original audio files
