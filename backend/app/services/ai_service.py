import google.generativeai as genai
import json
import os
import re

class AIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = None
        
        if not self.api_key:
            return  # Model will remain None; methods guard against this
        
        genai.configure(api_key=self.api_key)
        
        # Prefer gemini-2.5-flash for speed and cost, fallback to gemini-2.5-pro
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            print(f"Warning: gemini-2.5-flash initialization failed, falling back to gemini-2.5-pro: {e}")
            self.model = genai.GenerativeModel('gemini-2.5-pro')

    # -------------------------------------------------------------------------
    # NEW HELPERS — added for retry logic, temperature control, and validation.
    # Existing functions below are NOT modified; they only delegate to these.
    # -------------------------------------------------------------------------

    def _get_temperature(self, difficulty):
        """Maps difficulty level to a Gemini generation temperature."""
        temp_map = {'easy': 0.3, 'medium': 0.5, 'hard': 0.8}
        return temp_map.get(difficulty, 0.5)  # Default: medium

    def validate_response(self, data):
        """
        Validates an AI-generated response for required fields and non-emptiness.
        Returns (True, None) on success, (False, error_message) on failure.
        Checks single-question dicts and batch question arrays.
        """
        if not data:
            return False, "Response is empty"

        if isinstance(data, dict):
            required_fields = ['text', 'correct_answer']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return False, f"Missing required fields: {missing}"

        elif isinstance(data, list):
            if len(data) == 0:
                return False, "Response array is empty"
            for i, item in enumerate(data):
                required_fields = ['text', 'correct_answer']
                missing = [f for f in required_fields if not item.get(f)]
                if missing:
                    return False, f"Item {i} missing required fields: {missing}"

        return True, None

    def _call_with_retry(self, prompt, difficulty='medium', max_attempts=3):
        """
        Wraps self.model.generate_content() with retry logic and temperature
        control.  Uses the SAME prompt passed in — no modification.
        Raises the last encountered exception if all attempts are exhausted.
        """
        temperature = self._get_temperature(difficulty)
        generation_config = genai.types.GenerationConfig(temperature=temperature)

        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                if response and response.text:
                    return response  # Valid response — stop retrying
                last_error = ValueError("Empty response from Gemini AI.")
                print(f"AI call attempt {attempt}/{max_attempts} returned empty response, retrying...")
            except Exception as e:
                last_error = e
                print(f"AI call attempt {attempt}/{max_attempts} failed: {e}")

        # All retries exhausted — surface a clear structured error
        raise ValueError(
            f"AI generation failed after {max_attempts} attempts. "
            f"Last error: {last_error}"
        )


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
            response = self._call_with_retry(prompt, difficulty)  # retry + temperature control
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

            parsed = json.loads(json_str)
            is_valid, error_msg = self.validate_response(parsed)  # output validation
            if not is_valid:
                raise ValueError(f"AI response validation failed: {error_msg}")
            return parsed
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
            response = self._call_with_retry(prompt)  # retry + temperature control (medium default)
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
            is_valid, error_msg = self.validate_response(questions)  # output validation
            if not is_valid:
                raise ValueError(f"AI batch response validation failed: {error_msg}")
            return questions
        except Exception as e:
            print(f"AI Batch Generation Error: {str(e)}")
            raise e
