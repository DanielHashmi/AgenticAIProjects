from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, TResponseInputItem, input_guardrail, InputGuardrailTripwireTriggered, OpenAIChatCompletionsModel, set_tracing_disabled, AsyncOpenAI
from pydantic import BaseModel
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

class ResponseOutputType(BaseModel):
    bad_word_detected: bool

bad_word_detector_agent = Agent(
    name="Bad Word Detector Guardrail",
    instructions='You detect bad words.',
    output_type=ResponseOutputType,
    model=model
)

@input_guardrail
async def bad_word_detector_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    detection_result = await Runner.run(bad_word_detector_agent, input)

    return GuardrailFunctionOutput(
        tripwire_triggered=detection_result.final_output.bad_word_detected,
        output_info=detection_result.final_output
    )

assistant = Agent(
    name="Assistant Agent",
    instructions="You are a assistant agent, you help people.",
    model=model,
    input_guardrails=[bad_word_detector_guardrail]
)

try:
    result = await Runner.run(assistant, 'You are good!')
    print(result.final_output)
except InputGuardrailTripwireTriggered:
    print('Bad word detected!!')
