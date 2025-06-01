from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled, function_tool, RunContextWrapper, TResponseInputItem
import os
import dotenv
from dataclasses import dataclass
from random import randint

dotenv.load_dotenv()
set_tracing_disabled(disabled=True)

api_key = os.environ.get("GEMINI_API_KEY")

client = AsyncOpenAI(
    api_key=api_key,
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/'
)

model = OpenAIChatCompletionsModel('gemini-1.5-flash', client)

@dataclass
class UserProfile:
    id: str
    name: str
    balance: float
    cart: list[str]
    

@function_tool
def get_balance(wrapper: RunContextWrapper[UserProfile]):
    print('Getting balance...')
    return wrapper.context.balance

@function_tool
def deduct_balance(wrapper: RunContextWrapper[UserProfile], amount: int):
    print('Deducting balance...')
    wrapper.context.balance -= amount

@function_tool
def get_cart_items(wrapper: RunContextWrapper[UserProfile]):
    print('Getting items...')
    return wrapper.context.cart

@function_tool
def find_item_price(wrapper: RunContextWrapper[UserProfile], item: str):
    print('Finding item price...')
    return randint(1, 100)

@function_tool
def add_to_cart(wrapper: RunContextWrapper[UserProfile], items: list[str]):
    print('Adding to cart...')
    wrapper.context.cart.extend(items)
    return wrapper.context.cart

@function_tool
def remove_from_cart(wrapper: RunContextWrapper[UserProfile], items: list[str]):
    print('Removing from cart...')
    for item in items:
        wrapper.context.cart.remove(item)
        
    return wrapper.context.cart


shopping_agent = Agent(
    name='Shopping Agent',
    instructions='You are a shopping agent, You find items, their prices and help customers purchase them.',
    tools=[get_balance, get_cart_items, find_item_price, add_to_cart, remove_from_cart, deduct_balance],
    model=model
)

chat_history: list[TResponseInputItem] = []
user_profile: UserProfile = UserProfile(id='1234', name='Daniel Hashmi', balance=100, cart=[])


while True:
    customer = input('Customer: ')
    
    if customer == 'exit':
        print("Thanks for shopping!")
        break
    
    print(f"Customer: {customer}")
    
    chat_history.append({'role': 'user', 'content': customer})
    
    result = await Runner.run(shopping_agent, chat_history, context=user_profile)
    
    print(f"{result.last_agent.name}: {result.final_output}")
    
    chat_history = result.to_input_list()
