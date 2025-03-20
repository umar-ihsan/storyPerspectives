from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()
hf_api_key = os.getenv("HF_HOME")

app = FastAPI()

MONGO_URI = "mongodb+srv://jamshidjunaid763:JUNAID12345@insightwirecluster.qz5cz.mongodb.net/?retryWrites=true&w=majority&appName=InsightWireCluster"
client = MongoClient(MONGO_URI)
db = client["Scraped-Articles-11"]
articles_collection = db["Articles"]
bias_guidelines_collection = db["bias-guidelines"]

hf_client = InferenceClient(model="mistralai/Mistral-7B-Instruct-V0.3", token=hf_api_key)

class ArticleRequest(BaseModel):
    article_id: str
    bias_tag: str

def get_article(article_id: str):
    try:
        article = articles_collection.find_one({"_id": ObjectId(article_id)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid article ID format: {str(e)}")
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article["content"]

def get_bias_guidelines():
    guidelines = bias_guidelines_collection.find_one({"_id": ObjectId("67db1d2e5289edab40beae87")})
    if not guidelines:
        raise HTTPException(status_code=500, detail="Bias guidelines not found")
    return guidelines["content"]

def rewrite_article(original_text: str, bias_target: str, guidelines: str):
    prompt = f"""
    You are an expert news editor skilled in rewriting articles with specific political biases. 
    Given an article, rewrite it with the following bias: {bias_target}.
    
    Use these bias writing guidelines:
    {guidelines}
    
    Original Article:
    {original_text}
    
    Rewritten Article:
    """
    response = hf_client.text_generation(prompt, max_new_tokens=1024)
    return response

@app.post("/rewrite")
def rewrite_article_api(request: ArticleRequest):
    original_article = get_article(request.article_id)
    guidelines = get_bias_guidelines()
    opposite_bias = "left" if request.bias_tag == "right" else "right"
    
    rewritten_opposite = rewrite_article(original_article, opposite_bias, guidelines)
    rewritten_center = rewrite_article(original_article, "center", guidelines)
    
    return {
        "original_bias": request.bias_tag,
        "rewritten_opposite": rewritten_opposite,
        "rewritten_center": rewritten_center
    }

