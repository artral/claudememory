import os
from dotenv import load_dotenv
load_dotenv()
from quickstart import Quickstart
from tool_weather import WeatherTool
from web_search import WebSearchTool
from computer_tool import ComputerTool
from tool_memory import MemoryTool
from tool_memoryPersistance import MemoryPersistenceTool
from agent.codereview_agent import CodereviewAgent
if __name__ == "__main__":   
     api_key = os.getenv("ANTHROPIC_API_KEY")
     if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in the environment variables.")
     
     
     #tool = MemoryPersistenceTool()
     #tool.conversation_loop()
     
     
     code_review_agent = CodereviewAgent(memory_path="./memory")
     import os
     print(os.getcwd())
     file_content = open("./src/my_file_2.jsx", "r", encoding="utf-8").read()
     code_review_agent.review_code(file_content, "my_file_2.jsx")