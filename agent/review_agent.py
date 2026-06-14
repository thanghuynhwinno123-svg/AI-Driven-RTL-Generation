from langchain_core.messages import HumanMessage, SystemMessage
from .model_config import model_for


class ReviewAgent:
    def __init__(self, invoke_llm, model=None):
        self.invoke_llm = invoke_llm
        self.model = model or model_for("review")

    async def summarize_run(self, log_tail: str):
        summary_sys = SystemMessage(content="Write a concise markdown summary of the run in Vietnamese. Include overall status and notable bugs fixed.")
        return (await self.invoke_llm([summary_sys, HumanMessage(content=f"Run Log:\n{log_tail}")], model=self.model)).content.strip()
