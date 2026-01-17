import os, asyncio
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

"""
async def main():
    chat_completion = await client.chat.completions.create(
        messages=[
                # Set an optional system message. This sets the behavior of the
                # assistant and can be used to provide specific instructions for
                # how it should behave throughout the conversation.
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                # Set a user message for the assistant to respond to.
                {
                    "role": "user",
                    "content": "Explain the importance of fast language models",
                }
            ],
        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",

        # Optional parameters
        # As the temperature approaches zero, the model will become
        # deterministic and repetitive.

        temperature=0.5,

        # The maximum number of tokens to generate. Requests can use up to
        # 2048 tokens shared between prompt and completion.

        max_completion_tokens=1024,


        # Controls diversity via nucleus sampling: 0.5 means half of all
        # likelihood-weighted options are considered.

        top_p=1,

        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".

        stop=None,

        # If set, partial message deltas will be sent.
        stream=False,
    )
    # Print the completion returned by the LLM.
    print(chat_completion.choices[0].message.content)
"""
# to get the critique for a message (pre-submission feedback)
async def get_user_argument() -> str:
    """
    A function to test check_argument() on the command-line.
    """
    return input("Enter your argument: ")

async def give_system_prompt(topic_of_debate: str):
    """
    Gives a SYSTEM PROMPT to Logos about the topic of the conversation and how and when to reply.
    """
    logos_system_prompt = f"""
    ROLE: You are Logos, the Impartial Arbiter of this debate for the topic {topic_of_debate}.
    MISSION: Maintain logical integrity. 

    ### THE DATA STREAM
    You will be provided with a chat history's last 5 messages.
    **CRITICAL RULE:** You must ONLY analyze the **VERY LAST MESSAGE**.
    The messages before it are just for context. They are dead to you. Do not judge them.

    ### PROTOCOL: WHEN TO SHOOT (Intervene)
    Reply with a critique ONLY if the most recent message commits a NEW logical felony:
    1. **Ad Hominem:** Attacking the person, not the argument.
    2. **Strawman:** Blatantly misrepresenting the opponent's position.
    3. **Looping:** Repeating the exact same point 3+ times.
    etc.

    ### PROTOCOL: WHEN TO HOLD FIRE (Reply "NO")
    You must reply "NO" (Silence) in these cases:
    1. **The Defense Clause:** If the most recent message is defending themselves (e.g., "I didn't say that", "That is a strawman", "Don't attack me"). **DO NOT DOUBLE-TAP.**
    2. **The History Clause:** If the fallacy exists in the history but the most recent message has moved on.
    3. **The Opinion Clause:** If the user is just stating a weak opinion or an unsourced claim. (We do not fact check).
    etc.

    ### THE "QUOTING" EXCEPTION:
    - If the Last User REPEATS an insult to ask about it (e.g., "Why did you call me stupid?"), **DO NOT INTERVENE**.
    - Mentioning a fallacy is not committing a fallacy.
    - If the Last User is asking a clarifying question, reply "NO".

    ### OUTPUT FORMAT
    - If no intervention is needed: Reply "NO"
    - If intervention is needed: Reply with a single, surgical question exposing the fallacy.
    - Format: "your critique"
    - Example: "<@123456789>, how does attacking the opponent's character refute their economic data?"
    """ 
    return logos_system_prompt


async def check_model_response(messages: list, model: str) -> str:
    chat_completion = await client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.7,
    )
    return chat_completion.choices[0].message.content


async def get_one_line_stance(persona1: str, persona2: str, topic: str, number: int) -> str:
    if number == 1:
        content_string = f"I am setting up a debate on '{topic}' between '{persona1}' and '{persona2}'. Write a 1-sentence Immutable Stance for {persona1} that is aggressive and consistent with their history and directly opposes {persona2}. No 'here's something that could work', reply with the one line itself. That's it."
    elif number == 2:
        content_string = f"I am setting up a debate on '{topic}' between '{persona1}' and '{persona2}'. Write a 1-sentence Immutable Stance for {persona2} that is aggressive and consistent with their history and directly opposes {persona1}. No 'here's something that could work', reply with the one line itself. That's it."
        
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content_string,
            }
        ],
        temperature=0.2,
        model="llama-3.1-8b-instant",
    )

    return chat_completion.choices[0].message.content

async def check_argument(messages: list) -> str:
    try:
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content
    except Exception as error:
        raise RuntimeError("API call error, details below: \n") from error 

if __name__ == "__main__":
    argument = asyncio.run(get_user_argument())
    critique = asyncio.run(check_argument(argument))
    print(critique)