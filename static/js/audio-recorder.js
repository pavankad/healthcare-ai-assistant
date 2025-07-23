/**
 * Browser Audio Recorder with Real-time Transcription
 * Integrates with EMR Voice Recording API
 */

class EMRAudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingInterval = null;
        this.chunkDuration = 5000; // 5 seconds per chunk
        this.noteId = null;
        this.patientId = null;
        
        // Check for browser compatibility
        this.checkCompatibility();
    }
    
    checkCompatibility() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Browser does not support audio recording');
        }
        
        if (!window.MediaRecorder) {
            throw new Error('Browser does not support MediaRecorder API');
        }
    }
    
    async startRecording(patientId, noteId) {
        try {
            this.patientId = patientId;
            this.noteId = noteId;
            
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Create MediaRecorder
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: 128000
            };
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            
            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processAudioChunk();
            };
            
            // Start recording in chunks
            this.isRecording = true;
            this.startChunkedRecording();
            
            console.log('Audio recording started');
            return true;
            
        } catch (error) {
            console.error('Error starting audio recording:', error);
            throw error;
        }
    }
    
    startChunkedRecording() {
        if (!this.isRecording) return;
        
        // Start recording this chunk
        this.audioChunks = [];
        this.mediaRecorder.start();
        
        // Stop this chunk after the specified duration
        setTimeout(() => {
            if (this.isRecording && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
                
                // Schedule next chunk
                setTimeout(() => {
                    if (this.isRecording) {
                        this.startChunkedRecording();
                    }
                }, 100); // Small delay between chunks
            }
        }, this.chunkDuration);
    }
    
    async processAudioChunk() {
        if (this.audioChunks.length === 0) return;
        
        try {
            // Create blob from audio chunks
            const audioBlob = new Blob(this.audioChunks, { type: this.getSupportedMimeType() });
            
            // Send audio for transcription
            await this.sendAudioForTranscription(audioBlob);
            
        } catch (error) {
            console.error('Error processing audio chunk:', error);
        }
    }
    
    async sendAudioForTranscription(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, `audio_chunk_${Date.now()}.webm`);
            formData.append('note_id', this.noteId);
            formData.append('patient_id', this.patientId);
            
            const response = await fetch('/api/voice/transcribe-audio', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.transcription && result.transcription.trim()) {
                    console.log('Transcription received:', result.transcription);
                    
                    // Add transcription to clinical note
                    await this.addTranscriptionToNote(result.transcription);
                }
            } else {
                console.error('Transcription request failed:', response.status);
            }
            
        } catch (error) {
            console.error('Error sending audio for transcription:', error);
        }
    }
    
    async addTranscriptionToNote(transcription) {
        try {
            const response = await fetch('/api/voice/add-transcription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    note_id: this.noteId,
                    transcription: transcription
                }),
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                console.log('Transcription added to note successfully');
                
                // Trigger UI update event
                const event = new CustomEvent('transcriptionAdded', {
                    detail: { transcription: transcription, noteId: this.noteId }
                });
                window.dispatchEvent(event);
            }
            
        } catch (error) {
            console.error('Error adding transcription to note:', error);
        }
    }
    
    stopRecording() {
        this.isRecording = false;
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.noteId = null;
        this.patientId = null;
        
        console.log('Audio recording stopped');
    }
    
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/mpeg'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // fallback
    }
    
    getRecordingState() {
        return {
            isRecording: this.isRecording,
            noteId: this.noteId,
            patientId: this.patientId
        };
    }
}

// Export for use in dashboard
window.EMRAudioRecorder = EMRAudioRecorder;
