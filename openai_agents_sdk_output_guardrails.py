from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, OutputGuardrailTripwireTriggered, RunContextWrapper, Runner, output_guardrail, set_tracing_disabled, AsyncOpenAI, OpenAIChatCompletionsModel
import os
import dotenv

dotenv.load_dotenv()
set_tracing_disabled(disabled=True)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("API key not found!!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/'
)

model = OpenAIChatCompletionsModel('gemini-2.0-flash', client)

class MessageOutput(BaseModel):
    response: str

class BadWordOutputType(BaseModel):
    bad_word_detected: bool
    bad_words_found: list[str]

bad_word_detector_agent = Agent(
    name="Bad Word Detector Agent",
    instructions="You are a bad word detector agent, you detect bad words like bad, mental, gross etc... in a given text.",
    model=model,
    output_type=BadWordOutputType
)

@output_guardrail
async def forbidden_words_guardrail(ctx: RunContextWrapper, agent: Agent, output: str) -> GuardrailFunctionOutput:
    print(f"Checking output for bad words: {output}")
    
    result = await Runner.run(bad_word_detector_agent, f"text: {output}")

    print(f"Bad words found: {result.final_output.bad_words_found}")

    return GuardrailFunctionOutput(
        output_info={
            "reason": "Output contains bad words.",
            "bad_words_found": result.final_output.bad_words_found,
        },
        tripwire_triggered=result.final_output.bad_word_detected,
    )

agent = Agent(
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    output_guardrails=[forbidden_words_guardrail],
    model=model,
)

try:
    await Runner.run(agent, "say 'bad'")
    print("Guardrail didn't trip - this is unexpected")
except OutputGuardrailTripwireTriggered:
    print("The agent said a bad word, he is fired.")
