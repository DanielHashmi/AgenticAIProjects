# Using Gemini through LiteLMM because Gemini API KEY doesn't support parallel_tool_calls

from agents import Agent, Runner, set_tracing_disabled, function_tool, ModelSettings  
import os  
import dotenv  
import asyncio

dotenv.load_dotenv()  
set_tracing_disabled(disabled=True)  
  
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')  
  
if not GEMINI_API_KEY:  
    raise ValueError("API key not found!!")  
  
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY  
  
@function_tool  
def greet():  
    print('Greet was called first!')
    return "Hello!"
      
@function_tool  
def expansive_computation():  
    print('Im an expansive computational program... i wasted your money 😈!')
    return 'i will consume time, money etc.. but will be ignored!'
      
assistant = Agent(  
    name='Assistant',  
    instructions='You are a friendly assistant!',  
    model="litellm/gemini/gemini-2.0-flash",
    tool_use_behavior="stop_on_first_tool",  
    tools=[expansive_computation, greet],  
    model_settings=ModelSettings(  
        tool_choice="auto",  
        parallel_tool_calls=True,
    )  
)  
      
async def run():
    result = await Runner.run(  
        assistant,  
        'call greet first then expansive_computation',  
    )  
    print(result.final_output)
    
def main():
    asyncio.run(run())

# Output:
# Greet was called first!
# Im an expansive computational program... i wasted your money 😈!
# Hello!
