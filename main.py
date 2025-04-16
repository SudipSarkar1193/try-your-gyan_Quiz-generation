import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from quiz_generation import generate_quiz  

# Configure logging before FastAPI
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Output to stdout
)
logger = logging.getLogger(__name__)


logging.getLogger().setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

app = FastAPI()

class QuizRequest(BaseModel):
    user_id: int
    topic: str
    num_questions: int
    difficulty: str

@app.post("/generate-quiz")
async def quiz_endpoint(request: QuizRequest):
    try:
        logger.info(f"Received quiz request: {request.dict()}")
        normalized_difficulty = request.difficulty.lower()
        if not (5 <= request.num_questions <= 20):
            logger.error(f"Invalid num_questions: {request.num_questions}")
            raise HTTPException(status_code=400, detail="Number of questions must be between 5 and 20")
        if normalized_difficulty not in ["easy", "medium", "hard"]:
            logger.error(f"Invalid difficulty: {request.difficulty}")
            raise HTTPException(status_code=400, detail=f"Difficulty must be easy, medium, or hard (got {request.difficulty})")
        
        result = await generate_quiz(request)
        logger.info(f"Returning quiz: {len(result.get('data', []))} questions")
        return result
    except HTTPException as e:
        logger.error(f"Validation error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))