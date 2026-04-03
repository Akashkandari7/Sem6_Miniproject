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
        You are an expert university professor creating exam questions for '{subject_name}' on the topic '{topic}'.
        
        CRITICAL RULES FOR QUESTION QUALITY:
        - DO NOT generate simple "Define X" or "What is Y" type questions. These are too basic.
        - Questions MUST require critical thinking, logical reasoning, or real-world application.
        - For MCQs: Use tricky distractors that test deep understanding, not just memorization. Include scenario-based or code-based questions where relevant.
        - For Short answers: Ask students to compare, contrast, justify, or explain WHY — not just WHAT.
        - For Long answers: Include case studies, real-world scenarios, design problems, or multi-step analysis.
        - Match the Bloom's taxonomy level to the difficulty: easy=understand/apply, medium=apply/analyze, hard=evaluate/create.
        - Make questions that a student who only memorized textbook definitions would FAIL, but a student who truly understands concepts would PASS.
        
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
            if not response or not response.text:
                raise ValueError("Empty response from Gemini AI.")
            
            content = response.text
            # More robust JSON extraction - look for code blocks first, then try raw regex
            json_str = ""
            
            # 1. Try to find content within ```json ... ``` or ``` ... ```
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                # 2. Fallback to finding anything between curly braces
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content # Try raw content if no braces found (unlikely for valid JSON)

            return json.loads(json_str)
        except json.JSONDecodeError as je:
            print(f"AI JSON Parse Error: {str(je)} | Content: {content}")
            raise ValueError(f"AI returned invalid JSON format: {str(je)}")
        except Exception as e:
            print(f"AI Generation Error: {str(e)}")
            raise e
    def generate_questions_batch(self, subject_name, topic, distribution):
        """
        Generates multiple questions at once based on a marks distribution.
        Distribution: {"1": 5, "3": 2, "5": 1}
        """
        if not self.api_key:
            raise ValueError("Gemini API Key is not configured.")

        # Construct a readable summary of requested questions
        req_summary = ", ".join([f"{count} questions of {marks} marks" for marks, count in distribution.items() if count > 0])
        
        prompt = f"""
        You are an expert university professor designing a challenging exam for '{subject_name}' based on the topic/syllabus:
        '{topic}'

        Requested Distribution:
        {req_summary}

        CRITICAL RULES FOR QUESTION QUALITY:
        1. NEVER generate simple recall questions like "Define X", "What is Y", or "List the types of Z". These are lazy and too easy.
        2. Every question MUST test conceptual understanding, logical reasoning, or practical application.
        3. For 1-mark MCQs: Create scenario-based or tricky conceptual questions with plausible distractors. Example: Instead of "What is normalization?", ask "A table has partial dependency on a composite key. Which normal form is violated?".
        4. For 3-mark short questions: Ask students to compare, contrast, justify, trace algorithms, or explain cause-effect relationships. Example: Instead of "Define deadlock", ask "Why can't the Banker's algorithm prevent starvation? Justify.".
        5. For 5-mark long questions: Include real-world scenarios, algorithm traces with given data, design problems, or case studies. Example: "Given the following page reference string, calculate page faults for FIFO, LRU, and Optimal. Which performs best and why?".
        6. For 10-mark questions: Require comprehensive analysis, multi-part design problems, or critical evaluation with pros/cons. Example: "Design a normalized database schema for a hospital management system. Show the ER diagram, convert to 3NF, and justify your design decisions.".
        7. Vary Bloom's levels — prefer apply/analyze/evaluate over remember/understand. At least 60% of questions should be at apply level or above.
        8. Questions should feel like real university exam questions, not textbook review questions.

        Format the output as a JSON ARRAY of objects. Each object must have this structure:
        {{
            "text": "The question text here",
            "question_type": "mcq" | "short" | "long",
            "blooms_level": "remember" | "understand" | "apply" | "analyze" | "evaluate" | "create",
            "difficulty": "easy" | "medium" | "hard",
            "marks": 5,
            "option_a": "Option A (only if MCQ)",
            "option_b": "Option B (only if MCQ)",
            "option_c": "Option C (only if MCQ)",
            "option_d": "Option D (only if MCQ)",
            "correct_answer": "Correct Option/Answer"
        }}

        Return ONLY the JSON array. No extra text or markdown.
        """

        try:
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                raise ValueError("Empty response from Gemini AI.")
            
            content = response.text
            # Extract JSON Array
            json_str = ""
            code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content

            questions = json.loads(json_str)
            if not isinstance(questions, list):
                raise ValueError("AI did not return a JSON array.")
            
            return questions
        except Exception as e:
            print(f"AI Batch Generation Error: {str(e)}")
            raise e
