import google.generativeai as genai
import json
import os
import re

class AIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_question(self, subject_name, topic, question_type, difficulty, marks):
        """
        Generates a question using Gemini AI and returns it as a dictionary.
        """
        if not self.api_key:
            raise ValueError("Gemini API Key is not configured.")

        prompt = f"""
        Generate a professional academic question for the subject '{subject_name}' on the topic '{topic}'.
        
        Constraints:
        - Question Type: {question_type} (options: mcq, short, long)
        - Difficulty: {difficulty} (options: easy, medium, hard)
        - Marks: {marks}
        
        Format the output as a JSON object with the following structure:
        {{
            "text": "The question text here",
            "question_type": "{question_type}",
            "blooms_level": "one of: remember, understand, apply, analyze, evaluate, create",
            "difficulty": "{difficulty}",
            "marks": {marks},
            "option_a": "Option A (only if MCQ else null)",
            "option_b": "Option B (only if MCQ else null)",
            "option_c": "Option C (only if MCQ else null)",
            "option_d": "Option D (only if MCQ else null)",
            "correct_answer": "Correct Option/Answer description"
        }}
        
        Return ONLY the JSON object. No extra text or markdown.
        """

        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from markdown if necessary
            content = response.text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            return json.loads(content)
        except Exception as e:
            print(f"AI Generation Error: {str(e)}")
            raise e
