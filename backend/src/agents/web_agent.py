import logging
from src.prompts import PromptEngine
from .agent_types import Parameter
from .agent import Agent, agent
from .tool import tool
from src.utils import Config
from src.utils import update_scratchpad
from src.utils.web_utils import search_urls, scrape_content, summarise_content
from .validator_agent import ValidatorAgent

logger = logging.getLogger(__name__)
config = Config()

engine = PromptEngine()


def web_general_search_core(search_query, llm, model) -> str:
    urls = search_urls(search_query, num_results=15)
    logger.info(f"URLs found: {urls}")
    if not urls:
        return ["No relevant information found on the internet for the given query."]
    update_scratchpad(result=urls, agent_name="WebAgent")
    for url in urls:
        content = scrape_content(url)
        if not content:
           continue
        update_scratchpad(result=content, agent_name="WebAgent")
        final_response = summarise_content(search_query, content, llm, model)
        if final_response:
            update_scratchpad(result=final_response, agent_name="WebAgent")
            is_valid = is_valid_answer(final_response, search_query)
            if (is_valid):
                return [final_response]
            else:
                continue
    return ["No relevant information found on the internet for the given query."]


@tool(
    name="web_general_search",
    description="Search the internet based on the query provided and then "
                "get the meaningful answer from the content found",
    parameters={
        "search_query": Parameter(
            type="string",
            description="The search query to find information on the internet",
        ),
    },
)
def web_general_search(search_query, llm, model) -> str:
    return web_general_search_core(search_query, llm, model)


def get_validator_agent() -> Agent:
    return ValidatorAgent(config.validator_agent_llm, config.validator_agent_model)


def is_valid_answer(answer, task) -> bool:
    is_valid = (get_validator_agent().invoke(f"Task: {task}  Answer: {answer}")).lower() == "true"
    return is_valid


@agent(
    name="WebAgent",
    description="This agent is responsible for handling web search queries and summarizing information from the web.",
    tools=[web_general_search],
)
class WebAgent(Agent):
    pass
