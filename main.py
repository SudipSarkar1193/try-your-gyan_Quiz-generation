
from fastapi import FastAPI, HTTPException
#from fastapi.middleware.cors import CORSMiddleware
from quiz_generation import generate_quiz
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for React
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://127.0.0.1:5000","https://try-your-gyan-v2-1.onrender.com","https://try-your-gyan.vercel.app"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

class QuizRequest(BaseModel):
    user_id: int
    topic: str
    num_questions: int
    difficulty: str

@app.post("/generate-quiz")
async def quiz_endpoint(request: QuizRequest):
    logger.info("HIT THE SERVER")
    logger.info(f"Received request: {request.model_dump()}")
    try:
        # Normalize difficulty to lowercase
        normalized_difficulty = request.difficulty.lower()
        #logger.info(f"Normalized difficulty: {normalized_difficulty}")
        if not (5 <= request.num_questions <= 20):
            logger.error(f"Validation failed: Number of questions {request.num_questions} out of range (5-20)")
            raise HTTPException(status_code=400, detail="Number of questions must be between 5 and 20")
        if normalized_difficulty not in ["easy", "medium", "hard"]:
            logger.error(f"Validation failed: Difficulty {normalized_difficulty} not in ['easy', 'medium', 'hard']")
            raise HTTPException(status_code=400, detail=f"Difficulty must be easy, medium, or hard (got {request.difficulty})")
        
        result = await generate_quiz(request)
        return result
    
    except HTTPException as e:
        logger.error(f"Validation error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    

# Run with: uvicorn main:app --host 0.0.0.0 --port 8000