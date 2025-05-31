from agents import Agent, Runner, TResponseInputItem, handoff

def agent_invoked(ctx: RunContextWrapper):
    print('Handing off to other agent...')

fruit_expert_agent = Agent(
    name="Fruit Expert Agent",
    instructions="You are a fruit expert agent. Reply concisely.",
    model=model,
)

joke_writer_agent = Agent(
    name="Joke Writer Agent",
    instructions="You are a joke writer agent. Reply concisely.",
    model=model,
)

alice = Agent(
    name="Alice",
    instructions="You are a friendly assistant. Reply concisely.",
    model=model,
    handoffs=[handoff(fruit_expert_agent, on_handoff=agent_invoked), handoff(joke_writer_agent, on_handoff=agent_invoked)]
)

conversation: list[TResponseInputItem] = []
last_agent = alice

while True:
    user = input('You: ')
    
    if user == 'exit':
        print('Nice to meat you, Bye!')
        break
    
    print(f'You: {user}')
    
    conversation.append({'role':'user', 'content': user})
    
    result = await Runner.run(alice, conversation)
    print(f'{result.last_agent.name}: {result.final_output}')
    
    last_agent = result.last_agent
    conversation = result.to_input_list()
