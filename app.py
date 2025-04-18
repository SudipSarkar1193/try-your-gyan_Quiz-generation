import logging
import os
import asyncio
from flask import Flask, request, jsonify
from quiz_generation import generate_quiz
import psutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-quiz', methods=['POST'])
def quiz_endpoint():
    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        logger.info(f"Memory usage before quiz generation: {mem_info.rss / 1024 / 1024:.2f} MB")

        data = request.get_json()
        logger.info(f"Received quiz request: {data}")

        # Validation
        user_id = data.get("user_id")
        topic = data.get("topic")
        num_questions = data.get("num_questions")
        difficulty = data.get("difficulty", "").lower()

        if not (5 <= num_questions <= 20):
            logger.error(f"Invalid num_questions: {num_questions}")
            return jsonify({"error": "Number of questions must be between 5 and 20"}), 400
        
        if difficulty not in ["easy", "medium", "hard"]:
            logger.error(f"Invalid difficulty: {difficulty}")
            return jsonify({"error": "Difficulty must be easy, medium, or hard"}), 400
        
        result = generate_quiz(data)
        logger.info(f"Returning quiz: {len(result.get('data', []))} questions")
        
        mem_info = process.memory_info()
        logger.info(f"Memory usage after quiz generation: {mem_info.rss / 1024 / 1024:.2f} MB")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
