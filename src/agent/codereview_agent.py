import time
import threading
from typing import Optional

from pydantic import TypeAdapter

from anthropic import Anthropic
from anthropic.tools import BetaLocalFilesystemMemoryTool
from anthropic.types.beta import (
    BetaMemoryTool20250818ViewCommand,
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818StrReplaceCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818RenameCommand,
)
COMMAND_MAP = {
    "view": BetaMemoryTool20250818ViewCommand,
    "create": BetaMemoryTool20250818CreateCommand,
    "insert": BetaMemoryTool20250818InsertCommand,
    "str_replace": BetaMemoryTool20250818StrReplaceCommand,
    "delete": BetaMemoryTool20250818DeleteCommand,
    "rename": BetaMemoryTool20250818RenameCommand,
}



MEMORY_SYSTEM_PROMPT = """
- Store facts about recurring bug patterns and the developer's coding style
- Before reviewing, check memory for known patterns from past reviews
- Keep memories up-to-date; remove stale info
- Do NOT store raw conversation history
- Use simple list format in memory files
"""

class CodereviewAgent:
    def __init__(self, memory_path: str = "./memory", config = None):
        self.config = config
        self.client = Anthropic()
        self.memory_path = memory_path
        self.memory = BetaLocalFilesystemMemoryTool(base_path=self.memory_path)
        self.messages = []

    
    def review_code(self, code: str, filename: str):
        self.messages.append({
            "role": "user",
            "content": f"Review this file `{filename}`:\n```\n{code}\n```"
        })
        while True:
            response = self.client.beta.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                betas=["context-management-2025-06-27"],
                system=MEMORY_SYSTEM_PROMPT,
                messages=self.messages,
                tools=[self.memory.to_dict()],
                context_management={
                "edits": [
                    {
                        "type": "clear_tool_uses_20250919",
                        "trigger": {"type": "input_tokens", "value": 30000},
                        "keep": {"type": "tool_uses", "value": 3},
                    }
                ]
                }
            )           
    
                        # collect tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    command_name = block.input.get("command")
                    model_class = COMMAND_MAP[command_name]
                    parsed_command = TypeAdapter(model_class).validate_python(block.input)
                    command = model_class(**block.input)
                    result = self.memory.execute(command)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })

            self.messages.append({"role": "assistant", "content": response.content})
            if tool_results:
                self.messages.append({"role": "user", "content": tool_results})
            else:
                # Claude is done, extract final text
                for block in response.content:
                    if hasattr(block, "text"):
                        print(block.text)
                break


