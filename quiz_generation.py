from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StructuredOutputParser, ResponseSchema
import random
import os
from db import get_past_questions
import json
import asyncio
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the expected JSON structure
response_schemas = [
    ResponseSchema(name="ok", description="Success indicator", type="boolean"),
    ResponseSchema(
        name="data",
        description="Array of questions or error message",
        type="array"
    )
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Normalize topic to a canonical form
def normalize_topic(raw_topic: str) -> str:
    # Remove common quiz generation phrases and normalize
    topic = raw_topic.lower().strip()
    phrases_to_remove = [
        r"generate\s+me\s+a\s+quiz\s+on",
        r"create\s+a\s+quiz\s+about",
        r"quiz\s+on",
        r"a\s+quiz\s+on"
    ]
    for phrase in phrases_to_remove:
        topic = re.sub(phrase, "", topic)
    logger.info(f"Normalized topic from '{raw_topic}' to '{topic}'")
    return topic.strip() or "unknown"

# Quiz generation
async def generate_quiz(request):
    logger.info(f"Starting generate_quiz with request: {request.dict()}")
    print("in generate_quiz , request :", request.dict())  # Keep print for quick debugging

    # Normalize the topic
    normalized_topic = normalize_topic(request.topic)
    logger.info(f"Normalized topic: {normalized_topic}")
    print("in generate_quiz , normalized_topic :", normalized_topic)

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("API_KEY"),
        temperature=0.9,
    )
    logger.info("Gemini LLM initialized")

    # Fetch past questions using normalized topic
    loop = asyncio.get_event_loop()
    past_questions = await loop.run_in_executor(None, lambda: get_past_questions(request.user_id, normalized_topic))
    past_questions_str = "; ".join(past_questions) if past_questions else "None"
    logger.info(f"Past questions fetched: {past_questions_str}")

    # Dynamic prompt with randomization and history
    random_seed = random.randint(1, 1000)
    prompt = ChatPromptTemplate.from_messages([
        ("human", """
        Generate a quiz with the following details:
        - **Topic**: "{topic}"
        - **Number of Questions**: {num}
        - **Difficulty Level**: "{diff}"
        
        ### Instructions:
        1. Create an array of quiz questions in this JSON format: {format}
        2. Each question must include: serial_number (string), question, options (4 strings), correctAnswer, description.
        3. Use a creative twist (e.g., real-world scenarios, analogies) to add variety. Random seed: {seed}.
        4. Do NOT repeat these past questions: {past}.
        
        ### Guidelines:
        - Ensure content is accurate, clear, and matches the topic and difficulty.
        - If you can't generate the requested number, provide as many as possible.
        
        ### Fallback:
        - If the topic is inappropriate, return: [ {{ "ok": false }}, ["The requested topic is inappropriate or cannot be used."] ]
        
        Always return a two-element array: [ {{ "ok": bool }}, [questions or error] ].
        """)
    ])
    formatted_prompt = prompt.format(
        topic=normalized_topic,
        num=request.num_questions,
        diff=request.difficulty,
        format=output_parser.get_format_instructions(),
        seed=random_seed,
        past=past_questions_str
    )
    logger.info(f"Formatted prompt: {formatted_prompt.messages[0].content}")

    # Generate quiz
    try:
        logger.info("Invoking LLM with prompt")
        response = await llm.ainvoke(formatted_prompt)
        logger.info(f"LLM response raw content: {response.content}")
        parsed_response = output_parser.parse(response.content)
        logger.info(f"Parsed response: {parsed_response}")
        print("parsed_response:\n", parsed_response)

        if parsed_response["ok"]:
            if isinstance(parsed_response["data"][0], dict):
                logger.info("Returning valid quiz response")
                return parsed_response
            elif isinstance(parsed_response["data"][0], str):
                logger.error(f"Error in response data: {parsed_response['data'][0]}")
                raise Exception(parsed_response["data"][0])
            else:
                logger.error("Invalid response format")
                raise Exception("Invalid response format")
        else:
            logger.error("Quiz generation failed")
            raise Exception("Quiz generation failed")
    except Exception as e:
        logger.error(f"Exception in generate_quiz: {str(e)}")
        return [{"ok": False}, [f"Error generating quiz: {str(e)}"]]