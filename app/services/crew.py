import os
from autogen import AssistantAgent, UserProxyAgent

# Groq via OpenAI-compatible endpoint
GROQ_CONFIG = [{
    "model": "openai/gpt-oss-120b",
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "base_url": "https://api.groq.com/openai/v1",
    "api_type": "openai",
}]

def run_job_application_crew(job_url: str, user_resume: str) -> str:
    """
    Multi-agent pipeline using AutoGen:
    1. Researcher extracts job requirements
    2. Writer drafts cover letter
    3. Critic reviews and iterates until approved
    """
    llm_config = {
        "config_list": GROQ_CONFIG,
        "temperature": 0.7,
        "cache_seed": None,
    }

    researcher = AssistantAgent(
        name="Researcher",
        llm_config=llm_config,
        system_message=(
            "You are an expert tech recruiter. Read the job posting and identify "
            "the top 5 required technical skills and the main responsibilities. "
            "Then explicitly say 'Handing off to Writer.' to transfer control."
        ),
    )

    writer = AssistantAgent(
        name="Writer",
        llm_config=llm_config,
        system_message=(
            "You are a professional cover letter writer. Using the research, write "
            "a 3-paragraph cover letter tailored to the candidate's resume. "
            "Then explicitly say 'Handing off to Critic.' to transfer control."
        ),
    )

    critic = AssistantAgent(
        name="Critic",
        llm_config=llm_config,
        system_message=(
            "You are a hiring manager. Review the cover letter. "
            "If it's generic or missing skills, say 'REVISE: <feedback>' and hand off to Writer. "
            "If excellent, say 'APPROVED' and output the final letter."
        ),
    )

    # A single user proxy relays messages and runs the pipeline
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=6,
        code_execution_config=False,
        is_termination_msg=lambda msg: "APPROVED" in (msg.get("content") or "").upper(),
    )

    # Kick off the chain: user -> researcher -> writer -> critic
    response = user_proxy.initiate_chat(
        researcher,
        message=(
            f"Job URL: {job_url}\n\n"
            f"Candidate Resume:\n{user_resume}\n\n"
            "Start by researching the job. Then hand off to Writer. "
            "Writer hands off to Critic. Critic either approves or requests revision."
        ),
    )

    # Return the last message (should be the critic's APPROVED letter)
       # Return the full conversation transcript so you can see the Researcher,
    # Writer, and Critic's messages all together.
    transcript = []
    for msg in response.chat_history:
        role = msg.get("name", msg.get("role", "Agent"))
        content = msg.get("content", "")
        if content:
            transcript.append(f"--- {role} ---\n{content}")

    return "\n\n".join(transcript) if transcript else str(response)