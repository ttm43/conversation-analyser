import google.generativeai as genai
from google import genai as genai_client
from config import Config
import json
class ConversationAnalyzer:
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
            
        # Configure Gemini API
        genai.configure(api_key=config.gemini.api_key)
        
        # Initialize model and client
        self.model = genai.GenerativeModel(
            model_name=config.gemini.model_name,
            generation_config=config.gemini.generation_config
        )
        self.client = genai_client.Client(api_key=config.gemini.api_key)

    def analyze_audio(self, audio_data):
        """Analyze complete audio recording and generate transcript, Q&A, and summary"""
        try:
            # Create file part for upload
            audio_part = {
                'data': audio_data,
                'mime_type': 'audio/wav'
            }
            
            # Get complete analysis
            analysis_response = self.model.generate_content(
                contents=[
                    """Please analyze this medical consultation recording and provide the analysis in the following JSON format:

                    {
                        "transcript": [
                                {"speaker": "Doctor", "text": "Doctor's statement here"},
                                {"speaker": "Patient", "text": "Patient's response here"},
                                {"speaker": "Doctor", "text": "Doctor's next statement"},
                                ...
                            ],
                        "qa_analysis": {
                            "cause": {
                                "work": "answer about work posture/stress",
                                "sleep": "answer about sleep quality",
                                "sports_injuries": "answer about sports/hobbies injuries",
                                "mva": "answer about motor vehicle accidents",
                                "summary": "biggest cause summary"
                            },
                            "presentation": {
                                "main_complaint": "answer about main complaint by analyzing the whole conversation about: 
                                1. when do you feel the pain
                                2. where eactly do you feel the pain
                                3. how wuold you describe the pain (Achy, Stiff, Dull, Burning, Superficial, Numb, Tingling, Sharp, Deep, Clicking, Locking, Throbbing, Weakening, Shooting)",
                                "onset": "answer about when it started",
                                "is_chronic": "yes/no for >3 months"
                            },
                            "life_effect": {
                                "activities_impact": "answer about impact on daily activities by analyzing the whole conversation about: 
                                1. How does this problem affect your daily activities
                                2. How does this problem affect your work/study
                                3. How does this problem affect your sleep
                                4. How does this problem affect your hobbies/sports
                                5. How does this problem affect your mental state
                                6. How does this problem affect your relationships",
                                "nerve_root": "answer about nerve root symptoms",
                                "clumsy": "answer about clumsy symptoms",
                                "focus": "answer about focus issues",
                                "immune": "answer about immune system",
                                "stress": "answer about stress level"
                            },
                            "intent": {
                                "previous_care": "answer about previous care/adjustments",
                                "previous_exercises": "answer about previous exercises",
                                "lifestyle_changes": "answer about lifestyle/environment changes",
                                "why_not_healed": "answer about why not healed",
                                "goal": "answer about treatment goals by analyzing the whole conversation about:
                                1. What would you like to do more of once this problem is gone
                                2. Would you like to be more productive at work, sleep better, enjoy yor hobbies, get back into sports or exercise or just feel healthier and happier"
                            }
                        },
                        "summary": {
                            "presentation": "symptoms and conditions summary",
                            "life_effect": "impact on daily activities summary",
                            "goal": "treatment objectives summary, based on the (activities_impact) in (life_effect)
                            for example: if the patient says that the problem affects their work/study, then the goal should be more productive at work, if the patient says that the problem affects their sleep, then the goal should be better sleep, if the patient says that the problem affects their hobbies/sports, then the goal should be get back into sports or exercise, if the patient says that the problem affects their mental state, then the goal should be feel healthier and happier"
                        }
                    }
                    
                    Guidelines(must follow):

                    1. For the transcript:
                    - Use an array format with square brackets []
                    - Each entry should have "speaker" (either "Doctor" or "Patient") and "text" fields
                    - Keep each logical statement as a separate entry
                    - Identify speakers based on context, voice characteristics, and content

                    2. For the qa_analysis:
                    - Always analyze the whole conversation then provide answers
                    - Keep answers concise (1-2 sentences) but informative
                    - Use direct quotes from the patient when possible
                    - For yes/no questions, start with "Yes" or "No" followed by explanation
                    - If information is not mentioned in the recording, use "Not mentioned" instead of guessing
                    - The "summary" field in each section should synthesize the key points

                    3. For the summary section:
                    - "presentation" should focus on symptoms, duration, and severity
                    - "life_effect" should highlight the most significant impacts on daily life
                    - "goal" should clearly state what the patient hopes to achieve from treatment
                    - Each summary should be 2-3 sentences maximum

                    Please ensure the response is in valid JSON format.
                    """,
                    audio_part
                ]
            )
 
            # print(analysis_response.text)
            # Parse JSON response
            # Extract JSON from markdown code block
            response_text = analysis_response.text
            if '```json' in response_text:
                # Extract content between ```json and ```
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            else:
                # If no json marker, try to extract between ``` and ```
                json_str = response_text.split('```')[1].split('```')[0].strip()
                
            # Parse JSON
            analysis_data = json.loads(json_str)
            # print(analysis_data)
            return analysis_data
                
        # except Exception as e:
        #     print(f"Audio analysis error: {str(e)}")
        #     return None
        #     try:
        #         analysis_data = json.loads(analysis_response.text)
        #         return {
        #             'transcript': analysis_data.get('transcript', ''),
        #             'qa_analysis': {
        #                 'cause': analysis_data.get('qa_analysis', {}).get('cause', {}),
        #                 'presentation': analysis_data.get('qa_analysis', {}).get('presentation', {}),
        #                 'life_effect': analysis_data.get('qa_analysis', {}).get('life_effect', {}),
        #                 'intent': analysis_data.get('qa_analysis', {}).get('intent', {})
        #             },
        #             'summary': analysis_data.get('summary', {})
        #         }
        #     except json.JSONDecodeError as e:
        #         print(f"JSON parsing error: {str(e)}")
        #         return None
            
        except Exception as e:
            print(f"Audio analysis error: {str(e)}")
            return None