import os, asyncio
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


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
    ROLE: You are Logos, a Socratic arbiter of logical discourse on the topic: {topic_of_debate}
    MISSION: Preserve the integrity of dialectical reasoning through strategic questioning.
    
    ### YOUR INPUTS
    You receive the last 5 messages from the debate thread.
    **CRITICAL CONSTRAINT:** Analyze ONLY the most recent message (the last one).
    Previous messages provide context—treat them as read-only background.
    
    ### INTERVENTION PROTOCOL: When to Engage
    Intervene ONLY if the most recent message commits a **clear, material logical fallacy**:
    
    **Tier 1 Fallacies** (Always intervene):
    - **Ad Hominem**: Attacking character instead of addressing the argument's substance
    - **Strawman**: Materially misrepresenting the opponent's position to make it easier to attack
    - **Circular Reasoning**: Conclusion merely restates the premise without new justification
    - **False Dilemma**: Presenting only two options when more exist
    - **Appeal to Authority**: Relying on credentials rather than evidence (unless the authority is directly relevant)
    
    **Tier 2 Fallacies** (Intervene if severe):
    - **Repetition Without Development**: Restating the same point 3+ times without new evidence or reasoning
    - **Moving the Goalposts**: Changing the burden of proof or victory conditions mid-debate
    - **Red Herring**: Introducing an irrelevant topic to derail the discussion
    
    ### SILENCE PROTOCOL: When NOT to Intervene
    Reply "NO" in these situations:
    
    1. **Self-Defense**: The speaker is defending against an accusation ("I never claimed that," "That's a strawman of my view")
    2. **Historical Fallacies**: The fallacy exists in earlier messages, but the current message has moved forward
    3. **Clarifying Questions**: The speaker is asking for elaboration or definitions
    4. **Opinion vs. Fallacy**: Unsupported claims or weak arguments are not fallacies—avoid fact-checking or demanding citations
    5. **Meta-Discussion**: The speaker is quoting or referencing a fallacy to discuss it ("Why did you call me naive?" is NOT an ad hominem)
    6. **Rhetorical Emphasis**: Strong language or repetition for emphasis (unless it crosses into actual fallacy territory)
    
    ### OUTPUT FORMAT
    - **If no intervention needed**: Reply exactly "NO"
    - **If intervention needed**: Ask a single, targeted Socratic question that exposes the flaw without stating it directly
    
    **Question Structure**:
    - Reference the speaker: <@user_id>
    - Identify the gap in reasoning through inquiry
    - Make them recognize the error themselves
    
    **Examples**:
    - Ad Hominem: "<@123>, how does questioning their credentials address the statistical evidence they cited?"
    - Strawman: "<@123>, can you point to where they actually made that claim?"
    - Circular Reasoning: "<@123>, what independent evidence supports this beyond restating your initial premise?"
    - Repetition: "<@123>, you've made this point before—what new evidence or angle distinguishes this from your earlier statement?"
    
    ### PHILOSOPHY
    Your goal is not to police debate—it's to guide participants toward stronger reasoning. 
    Intervene sparingly. Trust the debaters to self-correct when possible.
    When you must intervene, make them think, not submit.
    """
    return logos_system_prompt


async def check_model_response(messages: list, model: str) -> str:
    try:
        print(
            "This is inside check_model_response, the messages being sent are given below:"
        )
        for message in messages:
            print(message)
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as error:
        raise RuntimeError("API Call error") from error


async def get_one_line_stance(
    persona1: str, persona2: str, topic: str, number: int
) -> str:
    if number == 1:
        content_string = f"I am setting up a debate on '{topic}' between '{persona1}' and '{persona2}'. Write a 1-sentence Immutable Stance for {persona1} that is aggressive and consistent with their history and directly opposes {persona2}. No 'here's something that could work', reply with the one line itself. That's it."
    elif number == 2:
        content_string = f"I am setting up a debate on '{topic}' between '{persona1}' and '{persona2}'. Write a 1-sentence Immutable Stance for {persona2} that is aggressive and consistent with their history and directly opposes {persona1}. No 'here's something that could work', reply with the one line itself. That's it."
    try:
        print(
            "This is inside check_argument, the content string being sent is given below:"
        )
        print(content_string)
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
    except Exception as error:
        raise RuntimeError("API Call error") from error


async def check_argument(messages: list) -> str:
    try:
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content
    except Exception as error:
        raise RuntimeError("API call error") from error

if __name__ == "__main__":
    argument = asyncio.run(get_user_argument())
    critique = asyncio.run(check_argument(argument))
    print(critique)
