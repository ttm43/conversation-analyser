import queue
import re
import sys
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.exceptions import NotFound
import pyaudio
import os
from dataclasses import dataclass
import threading
import wave
from datetime import datetime
import keyboard  # 添加这个导入
from conversation_analyzer import ConversationAnalyzer

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

@dataclass
class GCPConfig:
    """Google Cloud Platform configuration"""
    project_id: str
    credentials_path: str
    
    def __post_init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self._audio_interface = None
        self.paused = False
        self.recording_data = []  # 存储录音数据
        self.recording_filename = None

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        
        # 不再打印设备列表
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
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """音频数据回调"""
        if not self.paused:
            # 只计算音频电平，不输出
            audio_level = max(abs(int.from_bytes(in_data[i:i+2], byteorder='little', signed=True)) 
                            for i in range(0, len(in_data), 2))
            
            self._buff.put(in_data)
            self.recording_data.append(in_data)  # 保存录音数据
            
        return None, pyaudio.paContinue

    def pause(self):
        """暂停录音和转写"""
        self.paused = True

    def resume(self):
        """继续录音和转写"""
        self.paused = False

    def start_recording(self):
        """开始录音"""
        self.recording_data = []
        self.recording_filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        return self.recording_filename

    def save_recording(self):
        """保存录音文件"""
        if not self.recording_data:
            return None
            
        with wave.open(self.recording_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self._audio_interface.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self._rate)
            wf.writeframes(b''.join(self.recording_data))
        
        return self.recording_filename

    def generator(self):
        """生成音频数据流"""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            
            if not self.paused:
                data = [chunk]
                while True:
                    try:
                        chunk = self._buff.get(block=False)
                        if chunk is None:
                            return
                        data.append(chunk)
                    except queue.Empty:
                        break

                audio_data = b"".join(data)
                if len(audio_data) > 0:
                    yield audio_data

class SpeechToText:
    def __init__(self, config: GCPConfig):
        self.config = config
        self.client = SpeechClient()
        self.recognizer_name = None
        self.analyzer = ConversationAnalyzer()
        self.transcripts = []  # 存储所有转写文本
    
    def delete_recognizer(self, recognizer_id: str):
        """Delete an existing recognizer"""
        try:
            request = cloud_speech.DeleteRecognizerRequest(
                name=f"projects/{self.config.project_id}/locations/global/recognizers/{recognizer_id}"
            )
            self.client.delete_recognizer(request=request)
        except Exception as e:
            # 移除错误输出
            pass

    def get_or_create_recognizer(self, recognizer_id: str):
        """Get or create a recognizer"""
        try:
            # 先尝试删除已存在的
            try:
                request = cloud_speech.DeleteRecognizerRequest(
                    name=f"projects/{self.config.project_id}/locations/global/recognizers/{recognizer_id}"
                )
                self.client.delete_recognizer(request=request)
            except Exception:
                pass

            # 创建新的 recognizer
            request = cloud_speech.CreateRecognizerRequest(
                parent=f"projects/{self.config.project_id}/locations/global",
                recognizer_id=recognizer_id,
                recognizer=cloud_speech.Recognizer(
                    display_name="Medical Conversation Recognizer",
                    default_recognition_config=cloud_speech.RecognitionConfig(
                        explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                            encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=16000,
                            audio_channel_count=1
                        ),
                        language_codes=["en-US"],
                        model="medical_conversation",
                        features=cloud_speech.RecognitionFeatures(
                            enable_automatic_punctuation=True,
                            enable_word_confidence=True,
                            enable_word_time_offsets=True
                        )
                    ),
                ),
            )
            
            operation = self.client.create_recognizer(request=request)
            return operation.result()
            
        except Exception as e:
            # 移除错误输出
            raise

    def transcribe_streaming(self, on_audio_level=None, on_transcript=None, on_analysis=None):
        """Only record audio without real-time transcription"""
        try:
            # Create audio stream and start recording
            self.stream = MicrophoneStream(RATE, CHUNK)
            filename = self.stream.start_recording()
            print(f"Start recording: {filename}")
            
            with self.stream as stream:
                audio_generator = stream.generator()
                
                # Only process audio levels for visualization
                for content in audio_generator:
                    if on_audio_level:
                        audio_level = max(abs(int.from_bytes(content[i:i+2], byteorder='little', signed=True)) 
                                        for i in range(0, len(content), 2))
                        on_audio_level(audio_level)
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise

    def pause_recording(self):
        """暂停录音和转写"""
        if self.stream:
            self.stream.paused = True

    def resume_recording(self):
        """继续录音和转写"""
        if self.stream:
            self.stream.paused = False

    def stop_recording(self):
        """停止录音和转写"""
        if self.stream:
            filename = self.stream.save_recording()
            self.stream.closed = True
            self.stream = None
            return filename
        return None

if __name__ == "__main__":
    config = GCPConfig(
        project_id="elegant-door-451705-f9",
        credentials_path="elegant-door-451705-f9-806c1762c76f.json"
    )
    
    stt = SpeechToText(config)
    stt.transcribe_streaming() 





