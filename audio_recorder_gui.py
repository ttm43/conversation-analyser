import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pyaudio
import wave
import threading
import os
import time
from datetime import datetime
from conversation_analyzer import ConversationAnalyzer
import json

class AudioRecorderGUI:
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("Audio Recorder & Analyzer")
        self.root.geometry("800x600")  # Increased size for analysis display
        
        # Initialize analyzer
        self.analyzer = ConversationAnalyzer()
        
        # Audio configuration
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        # Recording state
        self.is_recording = False
        self.is_paused = False
        self.frames = []
        
        # PyAudio instance
        self.p = None
        self.stream = None
        
        # Time tracking
        self.start_time = None
        self.total_elapsed = 0
        
        # 修改保存位置为相对路径
        self.recordings_dir = "recordings"
        self.consultations_dir = "consultations"
        
        # Create directories if they don't exist
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs(self.consultations_dir, exist_ok=True)
        
        # Create GUI elements
        self.setup_gui()
        
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_gui(self):
        # Left panel for recording controls
        left_panel = ttk.Frame(self.root)
        left_panel.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.Y)
        
        # Status label with larger font
        self.status_var = tk.StringVar(value="Ready to Record")
        self.status_label = ttk.Label(
            left_panel, 
            textvariable=self.status_var,
            font=('Arial', 12)
        )
        self.status_label.pack(pady=20)
        
        # Timer label with larger font
        self.timer_var = tk.StringVar(value="00:00")
        self.timer_label = ttk.Label(
            left_panel, 
            textvariable=self.timer_var,
            font=('Arial', 24)
        )
        self.timer_label.pack(pady=10)
        
        # Buttons frame
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(pady=20)
        
        # Create styled buttons
        style = ttk.Style()
        style.configure('Record.TButton', foreground='red')
        style.configure('Stop.TButton', foreground='green')
        style.configure('Pause.TButton', foreground='orange')
        
        # Record button
        self.record_btn = ttk.Button(
            btn_frame,
            text="Record",
            style='Record.TButton',
            command=self.toggle_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Pause button
        self.pause_btn = ttk.Button(
            btn_frame,
            text="Pause",
            style='Pause.TButton',
            command=self.toggle_pause,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_btn = ttk.Button(
            btn_frame,
            text="Stop",
            style='Stop.TButton',
            command=self.stop_recording,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # File info label
        self.file_label = ttk.Label(
            left_panel,
            text="",
            wraplength=350
        )
        self.file_label.pack(pady=20)
        
        # Upload button
        self.upload_btn = ttk.Button(
            left_panel,
            text="Upload Recording",
            command=self.upload_recording
        )
        self.upload_btn.pack(pady=10)
        
        # Right panel for analysis display
        right_panel = ttk.Frame(self.root)
        right_panel.pack(side=tk.RIGHT, padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Analysis text area
        ttk.Label(right_panel, text="Analysis Results", font=('Arial', 12)).pack()
        self.analysis_text = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            width=50,
            height=25
        )
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
    def initialize_pyaudio(self):
        if self.p is None:
            self.p = pyaudio.PyAudio()
            
    def update_timer(self):
        if self.is_recording and not self.is_paused:
            current = time.time() - self.start_time
            elapsed = self.total_elapsed + current
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_var.set(f"{minutes:02d}:{seconds:02d}")
            self.root.after(100, self.update_timer)
            
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        
    def start_recording(self):
        try:
            self.initialize_pyaudio()
            
            # Reset recording state
            self.is_recording = True
            self.is_paused = False
            self.frames = []
            self.start_time = time.time()
            self.total_elapsed = 0
            
            # Open audio stream
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # Update GUI
            self.status_var.set("Recording...")
            self.record_btn.configure(state=tk.DISABLED)
            self.pause_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.NORMAL)
            self.file_label.configure(text="")
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            # Start timer
            self.update_timer()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.cleanup_recording()
            
    def toggle_pause(self):
        if not self.is_recording:
            return
            
        if self.is_paused:
            # Resume recording
            self.is_paused = False
            self.start_time = time.time()
            self.status_var.set("Recording...")
            self.pause_btn.configure(text="Pause")
            # Restart the timer
            self.update_timer()
        else:
            # Pause recording
            self.is_paused = True
            self.total_elapsed += time.time() - self.start_time
            self.status_var.set("Paused")
            self.pause_btn.configure(text="Resume")
            
    def record_audio(self):
        while self.is_recording:
            if not self.is_paused:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    print(f"Error recording: {e}")
                    break
                    
    def stop_recording(self):
        if not self.is_recording:
            return
            
        try:
            # Stop recording
            self.is_recording = False
            self.is_paused = False
            
            # Clean up audio stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Save recording
            if self.frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save audio file
                audio_filename = f"recording_{timestamp}.wav"
                audio_filepath = os.path.join(self.recordings_dir, audio_filename)
                
                # Save the audio file
                with wave.open(audio_filepath, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.p.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(self.frames))
                
                self.status_var.set("Analyzing recording...")
                self.file_label.configure(
                    text=f"Audio saved to:\n{os.path.abspath(audio_filepath)}"
                )
                
                # Start analysis in a separate thread
                threading.Thread(
                    target=self.analyze_recording,
                    args=(audio_filepath, timestamp),
                    daemon=True
                ).start()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
        finally:
            # Reset GUI
            self.record_btn.configure(state=tk.NORMAL)
            self.pause_btn.configure(state=tk.DISABLED, text="Pause")
            self.stop_btn.configure(state=tk.DISABLED)
            self.timer_var.set("00:00")
            
    def analyze_recording(self, audio_filepath, timestamp):
        try:
            print(f"\n=== start analyzing recording {timestamp} ===")
            print(f"audio file path: {audio_filepath}")
            
            # Read the audio file
            with open(audio_filepath, 'rb') as audio_file:
                audio_data = audio_file.read()
            print(f"audio file size: {len(audio_data)} bytes")
            
            print("calling LLM API...")
            # Get analysis from Gemini
            analysis = self.analyzer.analyze_audio(audio_data)
            
            if analysis:
                print("LLM API call success!")
                print("analysis results overview:")
                print(f"- transcript text length: {len(str(analysis.get('transcript', [])))}")
                print(f"- QA analysis items: {len(analysis.get('qa_analysis', {}))}")
                print(f"- summary items: {len(analysis.get('summary', {}))}")
                
                # Format analysis for display
                formatted_analysis = self.format_analysis(analysis)
                
                # Save analysis to JSON file in consultations folder
                analysis_filename = f"consultation_{timestamp}.json"
                analysis_filepath = os.path.join(self.consultations_dir, analysis_filename)
                
                with open(analysis_filepath, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)
                
                print(f"analysis results saved to: {analysis_filepath}")
                
                # Update GUI in main thread
                self.root.after(0, self.update_analysis_display, formatted_analysis)
                self.root.after(0, lambda: self.status_var.set(
                    f"Analysis complete! Saved to: {os.path.basename(analysis_filepath)}"
                ))
                # Update file label to show both paths
                self.root.after(0, lambda: self.file_label.configure(
                    text=f"Audio saved to:\n{os.path.abspath(audio_filepath)}\n\n"
                         f"Analysis saved to:\n{os.path.abspath(analysis_filepath)}"
                ))
            else:
                print("LLM API returned empty result!")
                self.root.after(0, lambda: self.status_var.set("Analysis failed"))
                
        except Exception as e:
            print(f"分析过程出错: {str(e)}")
            import traceback
            print("错误详细信息:")
            print(traceback.format_exc())
            self.root.after(0, lambda: self.status_var.set(f"Analysis error: {str(e)}"))
            
    def format_analysis(self, analysis):
        """Format the analysis data for display"""
        formatted = "=== ANALYSIS RESULTS ===\n\n"
        
        # 首先打印原始数据结构以便调试
        print("Raw analysis data structure:")
        print(json.dumps(analysis, indent=2))
        
        # 添加转录文本
        formatted += "TRANSCRIPT:\n"
        if isinstance(analysis.get('transcript', []), list):
            for entry in analysis.get('transcript', []):
                # 更灵活的数据访问
                speaker = entry.get('speaker', 'Unknown')
                text = entry.get('text', entry.get('content', ''))  # 尝试多个可能的键名
                formatted += f"{speaker}: {text}\n"
        else:
            # 如果transcript不是列表，直接添加为文本
            formatted += str(analysis.get('transcript', '')) + "\n"
        formatted += "\n"
        
        # 添加QA分析
        formatted += "ANALYSIS:\n"
        qa = analysis.get('qa_analysis', {})
        
        # 格式化每个部分
        for section, data in qa.items():
            formatted += f"\n{section.upper()}:\n"
            if isinstance(data, dict):
                for key, value in data.items():
                    formatted += f"- {key}: {value}\n"
            else:
                formatted += f"- {data}\n"
        
        # 添加摘要
        formatted += "\nSUMMARY:\n"
        summary = analysis.get('summary', {})
        if isinstance(summary, dict):
            for key, value in summary.items():
                formatted += f"- {key}: {value}\n"
        else:
            formatted += str(summary) + "\n"
            
        return formatted
        
    def update_analysis_display(self, text):
        """Update the analysis text area"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, text)
        
    def cleanup_recording(self):
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            finally:
                self.stream = None
        
        self.is_recording = False
        self.is_paused = False
        
    def on_closing(self):
        if self.is_recording:
            self.stop_recording()
        if self.p:
            self.p.terminate()
        self.root.destroy()
        
    def upload_recording(self):
        try:
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title="Select Audio Recording",
                filetypes=[("Wave files", "*.wav"), ("All files", "*.*")]
            )
            
            if file_path:
                self.status_var.set("Analyzing uploaded recording...")
                self.file_label.configure(
                    text=f"Analyzing file:\n{os.path.abspath(file_path)}"
                )
                
                # 获取时间戳用于保存分析结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 在新线程中开始分析
                threading.Thread(
                    target=self.analyze_recording,
                    args=(file_path, timestamp),
                    daemon=True
                ).start()
                
        except Exception as e:
            self.status_var.set(f"Upload error: {str(e)}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AudioRecorderGUI()
    app.run() 