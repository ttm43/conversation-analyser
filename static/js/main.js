let mediaRecorder;
let audioChunks = [];
const socket = io();

// 获取所有按钮元素
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const pauseButton = document.getElementById('pauseButton');
const resumeButton = document.getElementById('resumeButton');

// 获取可视化画布
const canvas = document.querySelector('.visualizer');
const canvasCtx = canvas.getContext('2d');
let audioContext;
let analyser;
let dataArray;
let animationId;

// 开始录音
startButton.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        // 设置音频可视化
        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        source.connect(analyser);
        analyser.fftSize = 2048;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        // 开始可视化
        visualize();

        // 收集音频数据
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        // 开始录音
        mediaRecorder.start();
        socket.emit('start_recording');

        // 更新按钮状态
        startButton.disabled = true;
        stopButton.disabled = false;
        pauseButton.disabled = false;
        resumeButton.disabled = true;

    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('Error accessing microphone. Please ensure microphone permissions are granted.');
    }
});

// 停止录音
stopButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // 停止可视化
        cancelAnimationFrame(animationId);
        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

        // 更新按钮状态
        startButton.disabled = false;
        stopButton.disabled = true;
        pauseButton.disabled = true;
        resumeButton.disabled = true;

        // 显示分析状态
        document.getElementById('analysisStatus').style.display = 'block';

        socket.emit('stop_recording');
    }
});

// 暂停录音
pauseButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.pause();
        
        // 停止可视化
        cancelAnimationFrame(animationId);

        // 更新按钮状态
        pauseButton.disabled = true;
        resumeButton.disabled = false;
    }
});

// 恢复录音
resumeButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'paused') {
        mediaRecorder.resume();
        
        // 恢复可视化
        visualize();

        // 更新按钮状态
        pauseButton.disabled = false;
        resumeButton.disabled = true;
    }
});

// 可视化函数
function visualize() {
    analyser.getByteTimeDomainData(dataArray);
    canvasCtx.fillStyle = 'rgb(200, 200, 200)';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'rgb(0, 0, 0)';
    canvasCtx.beginPath();

    const sliceWidth = canvas.width * 1.0 / analyser.frequencyBinCount;
    let x = 0;

    for (let i = 0; i < analyser.frequencyBinCount; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvas.height / 2;

        if (i === 0) {
            canvasCtx.moveTo(x, y);
        } else {
            canvasCtx.lineTo(x, y);
        }

        x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();

    animationId = requestAnimationFrame(visualize);
}

// 处理分析结果
socket.on('audio_analysis', (response) => {
    // 隐藏分析状态
    document.getElementById('analysisStatus').style.display = 'none';

    if (response.status === 'error') {
        alert(response.message);
        return;
    }

    const analysis = response.data;

    // Display Transcript
    const transcriptContent = document.getElementById('transcript-content');
    
    // 检查 transcript 是否为数组
    if (Array.isArray(analysis.transcript)) {
        // 数组格式 - 构建对话形式的HTML
        let transcriptHtml = '';
        analysis.transcript.forEach(item => {
            transcriptHtml += `<p><strong>${item.speaker}:</strong> ${item.text}</p>`;
        });
        transcriptContent.innerHTML = transcriptHtml;
    } else {
        // 如果不是数组，按原来方式处理
        transcriptContent.innerHTML = `<p>${analysis.transcript}</p>`;
    }

    // Display Q&A Analysis
    // CAUSE
    const causeContent = document.getElementById('cause-content');
    causeContent.innerHTML = `
        <div class="form-item">
            <label>Work:</label>
            <span>${analysis.qa_analysis.cause.work || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Sleep:</label>
            <span>${analysis.qa_analysis.cause.sleep || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Sports/Hobbies:</label>
            <span>${analysis.qa_analysis.cause.sports_injuries || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>MVA:</label>
            <span>${analysis.qa_analysis.cause.mva || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Summary:</label>
            <span>${analysis.qa_analysis.cause.summary || 'N/A'}</span>
        </div>
    `;

    // PRESENTATION
    const presentationContent = document.getElementById('presentation-content');
    presentationContent.innerHTML = `
        <div class="form-item">
            <label>Main Complaint:</label>
            <span>${analysis.qa_analysis.presentation.main_complaint || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Onset:</label>
            <span>${analysis.qa_analysis.presentation.onset || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Chronic:</label>
            <span>${analysis.qa_analysis.presentation.is_chronic || 'N/A'}</span>
        </div>
    `;

    // LIFE EFFECT
    const lifeEffectContent = document.getElementById('life-effect-content');
    lifeEffectContent.innerHTML = `
        <div class="form-item">
            <label>Activities Impact:</label>
            <span>${analysis.qa_analysis.life_effect.activities_impact || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Nerve Root:</label>
            <span>${analysis.qa_analysis.life_effect.nerve_root || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Clumsy:</label>
            <span>${analysis.qa_analysis.life_effect.clumsy || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Focus:</label>
            <span>${analysis.qa_analysis.life_effect.focus || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Immune:</label>
            <span>${analysis.qa_analysis.life_effect.immune || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Stress:</label>
            <span>${analysis.qa_analysis.life_effect.stress || 'N/A'}</span>
        </div>
    `;

    // INTENT
    const intentContent = document.getElementById('intent-content');
    intentContent.innerHTML = `
        <div class="form-item">
            <label>Previous Care:</label>
            <span>${analysis.qa_analysis.intent.previous_care || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Previous Exercises:</label>
            <span>${analysis.qa_analysis.intent.previous_exercises || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Lifestyle Changes:</label>
            <span>${analysis.qa_analysis.intent.lifestyle_changes || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Why Not Healed:</label>
            <span>${analysis.qa_analysis.intent.why_not_healed || 'N/A'}</span>
        </div>
        <div class="form-item">
            <label>Goal:</label>
            <span>${analysis.qa_analysis.intent.goal || 'N/A'}</span>
        </div>
    `;

    // Display Summary
    const summaryContent = document.getElementById('summary-content');
    summaryContent.innerHTML = `
        <div class="summary-item">
            <h4>Presentation</h4>
            <p>${analysis.summary.presentation}</p>
        </div>
        <div class="summary-item">
            <h4>Life Effect</h4>
            <p>${analysis.summary.life_effect}</p>
        </div>
        <div class="summary-item">
            <h4>Goal</h4>
            <p>${analysis.summary.goal}</p>
        </div>
    `;
});