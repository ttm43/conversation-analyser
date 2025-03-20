from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from audio_recorder import create_recorder
from conversation_analyzer import ConversationAnalyzer
import threading
import json
from config import Config
import base64
from consultation_recorder import ConsultationRecorder

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, ping_timeout=3600, ping_interval=10)

# Global variables
recorder = None
record_func = None
analyzer = None
is_recording = False

# 初始化 ConsultationRecorder
consultation_recorder = ConsultationRecorder()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_recording')
def handle_start_recording():
    global recorder, record_func, analyzer, is_recording
    try:
        config = Config()
        analyzer = ConversationAnalyzer(config)
        
        def on_audio_level(level):
            socketio.emit('audio_level', {'level': level})
        
        recorder, record_func = create_recorder(on_audio_level=on_audio_level)
        is_recording = True
        record_func()
        
    except Exception as e:
        socketio.emit('error', {'message': str(e)})

@socketio.on('pause_recording')
def handle_pause_recording():
    global recorder
    if recorder:
        recorder.pause()

@socketio.on('resume_recording')
def handle_resume_recording():
    global recorder
    if recorder:
        recorder.resume()

@socketio.on('stop_recording')
def handle_stop_recording():
    global recorder, analyzer
    if recorder:
        filename = recorder.stop()
        if filename:
            try:
                with open(filename, 'rb') as f:
                    audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                analysis = analyzer.analyze_audio(audio_base64)
                if analysis:
                    # 自动保存分析结果
                    consultation_recorder.save_consultation(analysis)
                    
                    socketio.emit('audio_analysis', {
                        'status': 'success',
                        'data': analysis
                    })
                else:
                    socketio.emit('audio_analysis', {
                        'status': 'error',
                        'message': 'Failed to analyze audio'
                    })
            except Exception as e:
                print(f"Audio analysis error: {str(e)}")
                socketio.emit('audio_analysis', {
                    'status': 'error',
                    'message': f"Audio analysis error: {str(e)}"
                })

if __name__ == '__main__':
    socketio.run(app, debug=True) 