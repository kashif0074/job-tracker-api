import json
import os

from groq import Groq
from sentence_transformers import SentenceTransformer
import os
# Prevent PyTorch from consuming all CPU/RAM threads
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ... rest of the imports (import json, from groq import Groq, etc.)
# Initialize Groq for chat
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Local Embedding Model (384 dimensions)
# It will download ~80MB the first time the container starts
_embedder = SentenceTransformer('all-MiniLM-L6-v2')

CHAT_MODEL = "openai/gpt-oss-120b"


def get_embedding(text: str) -> list[float]:
    """Generate a 384-dim vector using a local model (free, no API needed)."""
    text = text.replace("\n", " ").strip()
    vec = _embedder.encode(text)
    return [float(x) for x in vec.tolist()]


def extract_skills(job_description: str) -> dict:
    """Extract structured skills using Groq (Llama 3.3)."""
    prompt = f"""
    Analyze this job description and extract:
    1. Programming languages
    2. Frameworks
    3. AI/ML tools
    4. Experience level (Junior, Mid, Senior)

    Return ONLY a valid JSON object with keys:
    "languages", "frameworks", "ai_tools", "experience_level"

    If a category is not mentioned, use [].

    Job Description:
    {job_description}
    """

    response = groq_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    
    return json.loads(response.choices[0].message.content)