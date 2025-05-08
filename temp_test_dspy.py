import os, sys, logging 
import dspy 
import dspy_json_patch 
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/verify_dspy_model.log"), logging.StreamHandler()]) 
logger = logging.getLogger() 
 
try: 
    from dotenv import load_dotenv 
    load_dotenv('.env.dspy') 
 
    dspy.settings.experimental = True 
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1") 
    model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407") 
 
    logger.info(f"Configuring DSPy with {model_name} at {lm_studio_api}") 
    lm = dspy.LM(model_type="openai", model=model_name, api_base=lm_studio_api, api_key="dummy", config={"temperature": 0.1, "max_tokens": 100}) 
    dspy.configure(lm=lm) 
 
    class SimpleQA(dspy.Signature): 
        question = dspy.InputField() 
        answer = dspy.OutputField() 
 
    predictor = dspy.Predict(SimpleQA) 
    result = predictor(question="What is 2+2?") 
ECHO is off.
    logger.info(f"Result: {result}") 
    logger.info(f"Answer: {result.answer}") 
 
    if hasattr(result, 'answer') and "4" in result.answer: 
        logger.info("DSPy model verification successful!") 
        sys.exit(0) 
    else: 
        logger.error(f"Unexpected response: {result}") 
        sys.exit(1) 
except Exception as e: 
    logger.error(f"Error verifying DSPy model: {e}") 
    sys.exit(1) 
