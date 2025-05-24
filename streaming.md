Text generation
The Mistral models allows you to chat with a model that has been fine-tuned to follow instructions and respond to natural language prompts. A prompt is the input that you provide to the Mistral model. It can come in various forms, such as asking a question, giving an instruction, or providing a few examples of the task you want the model to perform. Based on the prompt, the Mistral model generates a text output as a response.

The chat completion API accepts a list of chat messages as input and generates a response. This response is in the form of a new chat message with the role "assistant" as output.

python
typescript
curl
No streaming
import os
from mistralai import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

chat_response = client.chat.complete(
    model = model,
    messages = [
        {
            "role": "user",
            "content": "What is the best French cheese?",
        },
    ]
)

print(chat_response.choices[0].message.content)

With streaming
import os
from mistralai import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

stream_response = client.chat.stream(
    model = model,
    messages = [
        {
            "role": "user",
            "content": "What is the best French cheese?",
        },
    ]
)

for chunk in stream_response:
    print(chunk.data.choices[0].delta.content)

With async
import asyncio
import os

from mistralai import Mistral


async def main():
    api_key = os.environ["MISTRAL_API_KEY"]
    model = "mistral-tiny"

    client = Mistral(api_key=api_key)

    response = await client.chat.stream_async(
        model=model,
        messages=[
             {
                  "role": "user",
                  "content": "Who is the best French painter? Answer in JSON.",
              },
        ],
    )
    async for chunk in response:
        if chunk.data.choices[0].delta.content is not None:
            print(chunk.data.choices[0].delta.content, end="")


if __name__ == "__main__":
    asyncio.run(main())

Chat messages
Chat messages (messages) are a collection of prompts or messages, with each message having a specific role assigned to it, such as "system," "user," "assistant," or "tool."

A system message is an optional message that sets the behavior and context for an AI assistant in a conversation, such as modifying its personality or providing specific instructions. A system message can include task instructions, personality traits, contextual information, creativity constraints, and other relevant guidelines to help the AI better understand and respond to the user's input. See the API reference for explanations on how to set up a custom system prompt.
A user message is a message sent from the perspective of the human in a conversation with an AI assistant. It typically provides a request, question, or comment that the AI assistant should respond to. User prompts allow the human to initiate and guide the conversation, and they can be used to request information, ask for help, provide feedback, or engage in other types of interaction with the AI.
An assistant message is a message sent by the AI assistant back to the user. It is usually meant to reply to a previous user message by following its instructions, but you can also find it at the beginning of a conversation, for example to greet the user.
A tool message only appears in the context of function calling, it is used at the final response formulation step when the model has to format the tool call's output for the user. To learn more about function calling, see the guide.
When to use user prompt vs. system message then user message?
You can either combine your system message and user message into a single user message or separate them into two distinct messages.
We recommend you experiment with both ways to determine which one works better for your specific use case.
Other useful features
The prefix flag enables prepending content to the assistant's response content. When used in a message, it allows the addition of an assistant's message at the end of the list, which will be prepended to the assistant's response. For more details on how it works see prefix.

The safe_prompt flag is used to force chat completion to be moderated against sensitive content (see Guardrailing).

A stop sequence allows forcing the model to stop generating after one or more chosen tokens or strings.