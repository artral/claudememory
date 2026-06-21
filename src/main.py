import os
from dotenv import load_dotenv
load_dotenv()
from quickstart import Quickstart
from tool_weather import WeatherTool
from web_search import WebSearchTool
from computer_tool import ComputerTool
from tool_memory import MemoryTool
from tool_memoryPersistance import MemoryPersistenceTool
if __name__ == "__main__":   
     api_key = os.getenv("ANTHROPIC_API_KEY")
     if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in the environment variables.")
     
     
     tool = MemoryPersistenceTool()
     tool.conversation_loop()
     
     