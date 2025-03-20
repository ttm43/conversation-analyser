import queue
import pyaudio
import wave
from datetime import datetime
from dataclasses import dataclass

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms chunks

class AudioRecorder:
    """Handles audio recording and visualization"""
    
    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self._audio_interface = None
        self.paused = False
        self.recording_data = []
        self.recording_filename = None

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        
        self.closed = False
        self.paused = False
        return self

    def __exit__(self, type, value, traceback):
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        if self._audio_interface:
            self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Audio data callback"""
        if not self.paused:
            # Calculate audio level for visualization
            audio_level = max(abs(int.from_bytes(in_data[i:i+2], byteorder='little', signed=True)) 
                            for i in range(0, len(in_data), 2))
            
            self._buff.put((in_data, audio_level))
            self.recording_data.append(in_data)
            
        return None, pyaudio.paContinue

    def start(self):
        """Start a new recording"""
        self.recording_data = []
        self.recording_filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        return self.recording_filename

    def pause(self):
        """Pause recording"""
        self.paused = True

    def resume(self):
        """Resume recording"""
        self.paused = False

    def stop(self):
        """Stop recording and save the file"""
        if not self.recording_data:
            return None
            
        try:
            with wave.open(self.recording_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self._audio_interface.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self._rate)
                wf.writeframes(b''.join(self.recording_data))
            
            return self.recording_filename
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return None

    def get_audio_data(self):
        """Generator yielding audio data and levels"""
        while not self.closed:
            data = self._buff.get()
            if data is None:
                return
            
            if not self.paused:
                yield data  # Returns tuple of (audio_data, audio_level)

def create_recorder(on_audio_level=None):
    """Factory function to create and set up a recorder instance"""
    recorder = AudioRecorder()
    
    def record_and_visualize():
        try:
            with recorder as stream:
                filename = stream.start()
                print(f"Recording started: {filename}")
                
                for audio_data, level in stream.get_audio_data():
                    if on_audio_level:
                        on_audio_level(level)
                        
        except Exception as e:
            print(f"Recording error: {str(e)}")
            return None
    
    return recorder, record_and_visualize

# Example usage:
if __name__ == "__main__":
    def print_level(level):
        print(f"Audio level: {level}")
    
    recorder, record_func = create_recorder(on_audio_level=print_level)
    record_func() 