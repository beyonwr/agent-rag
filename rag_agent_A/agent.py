import logging
import os

from google.adk.agents import Agent 
from google.adk.agents.callback_context import CallbackContext 
from google.adk.models import LlmRequest
from google.adk.models.lite_llm import LiteLlm 

from .tools import search_tech_reports
from .utils.log_utils import get_user_session_logger
from .utils.prompt_utils import get_prompt_yaml

logger = logging.getLogger(__name__)

ROOT_AGENT_PROMPT = get_prompt_yaml(tag="prompt")
GLOBAL_INSTRUCTION = get_prompt_yaml(tag="global_instruction")


def before_agent_callback(callback_context: CallbackContext):

    try:
        user_id = callback_context.user_id
        session_id = callback_context.session.id
        session_logger = get_user_session_logger(user_id, session_id)

        user_content = callback_context.user_content
        if user_content and user_content.parts:
            user_text = user_content.parts[0].text if user_content.parts[0].text else ""
            session_logger.info("User query: %s", user_text)
    except Exception:
        logger.debug("Failed to log user query in before_agent_callback", exc_info=True)


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
):

    try:
        user_id = callback_context.user_id
        session_id = callback_context.session.id
        session_logger = get_user_session_logger(user_id, session_id)

        num_contents = len(llm_request.contents) if llm_request.contents else 0
        session_logger.debug(
            "LLM request: agent=%s, contents_count=%d",
            callback_context.agent_name,
            num_contents,
        )
    except Exception:
        logger.debug("Failed to log in before_model_callback", exc_info=True)


root_agent = Agent(
    name="root_agent_NoTune",
    model=LiteLlm(
        model=os.getenv("ROOT_AGENT_MODEL", ""),
        api_base=os.getenv("ROOT_AGENT_API_BASE"),
        stream=False,
    ),
    instruction=ROOT_AGENT_PROMPT,
    global_instruction=GLOBAL_INSTRUCTION,
    tools=[search_tech_reports],
    before_agent_callback=before_agent_callback,
    before_model_callback=before_model_callback,
    output_key="result",
)