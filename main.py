import logging
import os
import asyncio
import shutil
import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from quiz_generation import generate_quiz

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Debug for detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

app = FastAPI()

# Health endpoint => RESOURCE MONITORING
@app.get("/health")
async def health():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    total, used, free = shutil.disk_usage("/")
    return {
        "status": "healthy",
        "memory_used_mb": memory.used / 1024 / 1024,
        "memory_total_mb": memory.total / 1024 / 1024,
        "cpu_percent": cpu,
        "disk_free_gb": free / 1024**3
    }

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
        
        # Log resource usage 
        # 6before and after quiz generation and enforce timeout
        process = psutil.Process()
        start_time = asyncio.get_event_loop().time()
        logger.debug(f"Starting quiz generation, memory: {process.memory_info().rss / 1024 / 1024} MB")
        
        # Run generate_quiz with a timeout (e.g., 300 seconds)
        result = await asyncio.wait_for(generate_quiz(request), timeout=300)
        
        duration = asyncio.get_event_loop().time() - start_time
        logger.debug(f"Quiz generation completed in {duration:.2f}s, memory: {process.memory_info().rss / 1024 / 1024} MB")
        
        logger.info(f"Returning quiz: {len(result.get('data', []))} questions")
        return result
    except asyncio.TimeoutError:
        logger.error("Quiz generation timed out after 300 seconds")
        raise HTTPException(status_code=504, detail="Quiz generation took too long")
    except HTTPException as e:
        logger.error(f"Validation error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1,  # Match Dockerfile
        log_level="debug",
        timeout_keep_alive=65
    )