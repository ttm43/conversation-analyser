from google import genai
import time
from datetime import datetime

class QAAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key="AIzaSyB94C-q7lixySRo7AopBGWx5OTq4-FK6EY")
        self.transcripts = []  # 存储所有转写文本
        self.last_analysis_time = datetime.now()
        self.analysis_interval = 10  # 每10秒分析一次
        self.qa_pairs = []  # 存储已确认的问答对

    def add_transcript(self, text, is_final):
        """添加新的转写文本"""
        if is_final:
            self.transcripts.append(text)
            self._try_analyze()

    def _try_analyze(self):
        """尝试分析累积的文本"""
        now = datetime.now()
        if (now - self.last_analysis_time).total_seconds() >= self.analysis_interval:
            self._analyze_transcripts()
            self.last_analysis_time = now

    def _analyze_transcripts(self):
        """分析转写文本中的问答对"""
        if not self.transcripts:
            return

        # 合并所有转写文本
        full_text = "\n".join(self.transcripts)
        
        try:
            response = self.client.models.generate_content(
                model='gemini-pro',
                contents=[
                    """Analyze this medical consultation transcript and extract all question-answer pairs.
                    Only include questions that have clear answers.
                    Format each pair as:
                    Q: [Doctor's question]
                    A: [Patient's answer]
                    
                    Also categorize each Q&A pair into one of these categories:
                    - CAUSE (Work, Sleep, Injuries)
                    - PRESENTATION (Symptoms, Duration)
                    - LIFE EFFECT (Activities, Nervous system)
                    - INTENT (Past treatments, Goal)
                    
                    Format:
                    Category: [category name]
                    Q: [question]
                    A: [answer]
                    ---
                    """,
                    full_text
                ]
            )
            
            print("\n新的分析结果:")
            print("=" * 50)
            print(response.text)
            
        except Exception as e:
            print(f"分析错误: {str(e)}")

def test_realtime_analysis():
    """测试实时分析"""
    analyzer = QAAnalyzer()
    
    # 模拟实时转写输入
    transcripts = [
        "Doctor: Hello. Could you tell me what brings you in today?",
        "Patient: I have shoulder pain. It's been bothering me for two to three months now.",
        "Doctor: How's your sleep?",
        "Patient: No major issues there.",
        "Doctor: When did your shoulder problems first start?",
        "Patient: It started back in high school, but it's gotten worse.",
        "Doctor: Has this been chronic for more than three months?",
        "Patient: Yes, it comes and goes.",
        "Doctor: Have you tried any treatment before?",
        "Patient: Yes, I've tried Chinese medicine and acupuncture."
    ]
    
    # 模拟实时接收转写文本
    for text in transcripts:
        print(f"\n接收到转写: {text}")
        analyzer.add_transcript(text, is_final=True)
        time.sleep(2)  # 模拟实时间隔

if __name__ == "__main__":
    test_realtime_analysis() 