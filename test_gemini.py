import os
from config import Config
from conversation_analyzer import ConversationAnalyzer
import base64

def test_audio_analysis():
    """Test audio analysis functionality"""
    print("\nTesting audio analysis...")
    
    try:
        # Initialize analyzer
        config = Config()
        analyzer = ConversationAnalyzer(config)
        
        # Read test audio file
        audio_file_path = "recording_20250317_121112.wav"
        if not os.path.exists(audio_file_path):
            print(f"Error: Test file {audio_file_path} not found")
            return
            
        # Read and encode audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Analyze audio
        print("Analyzing audio file...")
        analysis = analyzer.analyze_audio(audio_base64)
        
        if analysis:
            print("\n=== Analysis Results ===")
            
            print("\n1. Transcript:")
            print(analysis.get('transcript', 'No transcript available'))
            
            print("\n2. Q&A Analysis:")
            qa_analysis = analysis.get('qa_analysis', {})
            if qa_analysis:
                # Print CAUSE section
                print("\nCAUSE:")
                cause = qa_analysis.get('cause', {})
                print(f"Work: {cause.get('work', 'N/A')}")
                print(f"Sleep: {cause.get('sleep', 'N/A')}")
                print(f"Sports/Hobbies: {cause.get('sports_injuries', 'N/A')}")
                print(f"MVA: {cause.get('mva', 'N/A')}")
                print(f"Summary: {cause.get('summary', 'N/A')}")
                
                # Print PRESENTATION section
                print("\nPRESENTATION:")
                presentation = qa_analysis.get('presentation', {})
                print(f"Main Complaint: {presentation.get('main_complaint', 'N/A')}")
                print(f"Onset: {presentation.get('onset', 'N/A')}")
                print(f"Chronic: {presentation.get('is_chronic', 'N/A')}")
                
                # Print LIFE EFFECT section
                print("\nLIFE EFFECT:")
                life_effect = qa_analysis.get('life_effect', {})
                print(f"Activities Impact: {life_effect.get('activities_impact', 'N/A')}")
                print(f"Nerve Root: {life_effect.get('nerve_root', 'N/A')}")
                print(f"Clumsy: {life_effect.get('clumsy', 'N/A')}")
                print(f"Focus: {life_effect.get('focus', 'N/A')}")
                print(f"Immune: {life_effect.get('immune', 'N/A')}")
                print(f"Stress: {life_effect.get('stress', 'N/A')}")
                
                # Print INTENT section
                print("\nINTENT:")
                intent = qa_analysis.get('intent', {})
                print(f"Previous Care: {intent.get('previous_care', 'N/A')}")
                print(f"Previous Exercises: {intent.get('previous_exercises', 'N/A')}")
                print(f"Lifestyle Changes: {intent.get('lifestyle_changes', 'N/A')}")
                print(f"Why Not Healed: {intent.get('why_not_healed', 'N/A')}")
                print(f"Goal: {intent.get('goal', 'N/A')}")
            
            print("\n3. Summary:")
            summary = analysis.get('summary', {})
            if summary:
                print(f"\nPresentation: {summary.get('presentation', 'N/A')}")
                print(f"Life Effect: {summary.get('life_effect', 'N/A')}")
                print(f"Goal: {summary.get('goal', 'N/A')}")
            
            print("\nAnalysis completed successfully!")
            
        else:
            print("Error: Analysis failed")
            
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("Starting Gemini API test...\n")
    test_audio_analysis()
