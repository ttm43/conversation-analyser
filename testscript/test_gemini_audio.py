from google import genai

client = genai.Client(api_key="AIzaSyB94C-q7lixySRo7AopBGWx5OTq4-FK6EY")

myfile = client.files.upload(file='recording_20250222_213520.wav')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        """Analyze this medical consultation audio recording and provide a structured report with exactly these three sections:

        1. Presentation: 
           - Main complaints and symptoms
           - Onset and duration
           - Pain patterns and triggers

        2. Life Effect:
           - Impact on daily activities
           - Work/study impact
           - Quality of life changes

        3. Goal:
           - Short-term relief targets
           - Long-term management plans
           - Lifestyle modifications needed

        Format each section clearly and include specific details from the conversation.""",
        myfile,
    ]
)

print("\n音频分析结果:")
print("=" * 50)
print(response.text)