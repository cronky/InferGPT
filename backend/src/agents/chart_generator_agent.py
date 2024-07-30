import logging
from src.prompts import PromptEngine
from .agent import Agent, agent
from .tool import tool
from .agent_types import Parameter
from src.utils.log_publisher import LogPrefix, publish_log_info
import matplotlib.pyplot as plt
import os

logger = logging.getLogger(__name__)

engine = PromptEngine()

def generate_chart(question_intent, categorical_values, question_params, timeframe, llm, model) -> str:
    details_to_generate_chart_code = engine.load_prompt(
        "details-to-generate-chart-code",
        question_intent=question_intent,
        categorical_values=categorical_values,
        question_params=question_params,
        timeframe=timeframe
    )
    generate_chart_code_prompt = engine.load_prompt("generate-chart-code")
    generated_code = llm.chat(model, generate_chart_code_prompt, details_to_generate_chart_code)
    sanitised_script = sanitise_script(generated_code)
    logger.info(f"Sanitised script: {sanitised_script}")
    publish_log_info(LogPrefix.USER, f"Code generated by the LLM and sanitised: {sanitised_script}", __name__)

    try:

        local_vars = {}
        exec(sanitised_script, {}, local_vars)
        fig = local_vars.get('fig')

        if fig is None:
            raise ValueError("The generated code did not produce a figure named 'fig'.")
        output_dir = '/app/output'

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        logger.info("Saving the figure as 'output.png'")
        output_path = os.path.join(output_dir, "output.png")
        fig.savefig(output_path)
        logger.info(f"Figure saved successfully as {output_path}")

    except Exception as e:
        logger.error(f"Error during chart generation or saving: {e}")
        raise
    return "output.png"

def sanitise_script(script: str) -> str:
    if script.startswith("```python"):
        script = script[9:]
    if script.endswith("```"):
        script = script[:-3]
    return script.strip()

@tool(
    name="generate_code_chart",
    description="Generate Matplotlib bar chart code if the user's query involves creating a chart",
    parameters={
        "question_intent": Parameter(
            type="string",
            description="The intent the question will be based on",
        ),
        "categorical_values": Parameter(
            type="string",
            description="The categorical values the chart needs to represent",
        ),
        "question_params": Parameter(
            type="string",
            description="""
                The specific parameters required for the question to be answered with the question_intent
                or none if no params required
            """,
        ),
        "timeframe": Parameter(
            type="string",
            description="string of the timeframe to be considered or none if no timeframe is needed",
        ),
    }
)

async def generate_code_chart(question_intent, categorical_values, question_params, timeframe, llm, model):
    return await generate_chart(question_intent, categorical_values, question_params, timeframe, llm, model)

@agent(
    name="CharGeneratorAgent",
    description="This agent is responsible for creating charts",
    tools=[generate_code_chart]
)

class CharGeneratorAgent(Agent):
    pass
