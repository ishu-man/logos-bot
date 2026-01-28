import discord, os, intelligence, asyncio, time
from discord import app_commands
from dotenv import load_dotenv
from groq import AsyncGroq

from keep_alive import keep_alive  # NEW

load_dotenv()
DISCORD_APP_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEST_GUILD = discord.Object(id=1457450076812349672)  # for somerville's suite
groq_client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

keep_alive()  # Test command


class LogosClient(discord.Client):
    user: discord.Client.user

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()  # global sync
        self.tree.copy_global_to(guild=TEST_GUILD)
        await self.tree.sync(guild=TEST_GUILD)


intents = discord.Intents.default()
client = LogosClient(intents=intents)


@client.tree.command()
async def test(interaction: discord.Interaction):
    """
    A secret message!
    """
    tic = time.perf_counter()
    await interaction.response.defer(ephemeral=True)
    toc = time.perf_counter()
    await interaction.followup.send(
        content=f"Logos is online with a latency of: {toc - tic:0.4f} seconds",
        ephemeral=True,
    )


@client.tree.command(
    name="debate",
    description="The main command for starting a debate and having Logos monitor it",
)
async def debate(
    interaction: discord.Interaction, member: discord.Member, *, topic: str
):
    await interaction.response.defer()

    channel = interaction.channel
    thread = await channel.create_thread(name=f"{topic}")
    author = interaction.user
    thread.invitable = True
    await thread.add_user(author)
    await thread.add_user(member)
    await thread.edit(slowmode_delay=30)

    # see if Logos is added as a participant
    if member.id == client.user.id:
        print("Logos is a member.")
        await interaction.followup.send(
            f'A private debate thread for **"{topic}"** has been created. Logos is participating as your opponent, not as a referee. {author.mention}, proceed to the thread.'
        )
        await thread.send(f"""I am ready.
The topic for this discussion is **\"{topic}\"**
I am your opponent. I will challenge your reasoning at every turn. Standard assistance tools like `/argue` remain available.
_State your opening premise._""")

        await asyncio.create_task(
            thread_with_logos_participating(thread=thread, topic=topic)
        )

    else:
        bot_response = f"""**Private Debate Room**
Topic: **\"{topic}\"**
I am monitoring this discussion for logical fallacies. I will intervene with questions when I detect flawed reasoning.
_The goal is truth, not victory._
Use `/argue` to test your arguments before posting them.

{author.mention} and {member.mention}, begin when ready."""
        await interaction.followup.send(
            f'A debate session with the topic "{topic}" and participants {author.mention} and {member.mention} has been created. Proceedings have moved to a private thread. Please continue the discussion there.'
        )
        await thread.send(bot_response)

        await asyncio.create_task(
            get_feedback_on_last_thread_message(thread=thread, topic=topic)
        )


async def get_feedback_on_last_thread_message(thread: discord.Thread, topic: str):
    analyzed_message_ID = 0
    messages = [
        {"role": "system", "content": await intelligence.give_system_prompt(topic)}
    ]
    previous_user_ID = 0
    while True:
        last_five_messages = [message async for message in thread.history(limit=5)]
        latest_message = last_five_messages[0]  # newest first.
        current_user_ID = latest_message.author.id
        if (latest_message.id != analyzed_message_ID) and (
            current_user_ID != client.user.id
        ):
            # check if the message was sent by the bot and check if it has already been analyzed
            if current_user_ID == previous_user_ID:
                print("THEY ARE THE SAME!!!")
                await latest_message.delete()
                await thread.send(
                    f"{latest_message.author.mention}, this is a **turn-based debate**. Please wait for your opponent to respond before posting again."
                )
                analyzed_message_ID = latest_message.id
                await asyncio.sleep(10)
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": f"{latest_message.author.mention}:{latest_message.clean_content}",
                    }
                )
                if len(messages) > 5:
                    messages = prune_messages(messages)

                for i in range(len(messages) - 1):
                    message = messages[i]
                    if message["role"] == "user":
                        message["content"] += "** READ ONLY **"

                logos_feedback = await intelligence.check_argument(messages=messages)

                if logos_feedback.startswith("NO"):
                    await asyncio.sleep(5)
                else:
                    await thread.send(content=logos_feedback)
        analyzed_message_ID = latest_message.id
        previous_user_ID = find_previous_user(last_five_messages)
        await asyncio.sleep(5)


def prune_messages(messages: list):
    length = len(messages)
    new_messages_list = [messages[0]]
    for i in range(length - 4, length):
        new_messages_list.append(messages[i])
    return new_messages_list


def find_previous_user(last_five_messages: list[discord.Message]):
    for message in last_five_messages:
        if message.author.id != client.user.id:
            return message.author.id
    return client.user.id


@client.tree.command(
    name="argue",
    description="Gives the user a personal feedback from the bot on how to better strengthen their argument",
)
async def argue(interaction: discord.Interaction, argument: str):
    older_messages = [message async for message in interaction.channel.history(limit=5)]

    messages = [
        {
            "role": "system",
            "content": f"""ROLE: You are Logos, a precision argument optimizer.
                MISSION: Transform the user's input into its most defensible form.
                
                ### YOUR INPUTS
                - [DEBATE CONTEXT]: Last 5 messages from the channel (may be empty if invoked outside a thread)
                - [USER INPUT]: The argument or question the user submitted
                
                ### OPTIMIZATION PROCESS
                
                **Step 1: Classify the Input**
                - Is this a **question** (seeking information)?
                - Is this an **argument** (making a claim)?
                - Is this a **rebuttal** (responding to an opponent)?
                
                **Step 2: Analyze Weaknesses**
                Evaluate the input against these criteria:
                - **Logical structure**: Does it contain fallacies or unsupported leaps?
                - **Concision**: Is it bloated with unnecessary words or emotion?
                - **Relevance**: Does it address the opponent's actual position (if context exists)?
                - **Vulnerability**: What counterarguments does it leave open?
                
                **Step 3: Optimize**
                - Remove emotional language that weakens credibility
                - Tighten phrasing without losing substance
                - Anticipate and preempt counterarguments
                - Ensure claims are defensible or properly hedged
                
                ### OUTPUT RULES
                
                **For Questions:**
                - Answer the question directly in 1-2 sentences
                - No "Critique" or "Optimized" sections
                
                **For Arguments/Rebuttals:**
                Use this exact format:
                
                **Weakness:** [One precise sentence identifying the core flaw—be surgical, not vague]
                **Optimized:** [The refined argument, maximum 3 sentences, stripped of fat and fortified against attack]
                
                **Constraints:**
                - NO preamble ("Here's a better version," "I've refined this for you")
                - NO pleasantries or fluff
                - The "Optimized" version must be **actionable**—they should be able to copy-paste it
                - If the input is already strong, say: "Weakness: None identified. This argument is defensible as-is."
                
                ### EXAMPLES
                
                **Input**: "You're wrong because you don't understand basic economics and clearly haven't read any real economists."
                **Weakness:** Ad hominem attack without engaging the economic argument itself.
                **Optimized:** "The data suggests a different conclusion—can you clarify which economic model supports your position?"
                
                **Input**: "I think maybe climate change might be a problem but I'm not totally sure because some people say it's natural cycles."
                **Weakness:** Hedging language and undefined opposition undermine the claim's force.
                **Optimized:** "Climate models show human activity as the dominant driver of recent warming. Natural cycles exist, but the rate and magnitude of current change exceed historical baselines."
                
                ### PHILOSOPHY
                Your job is to **sharpen, not replace**. Preserve the user's voice and intent while eliminating weaknesses.
                If the context shows the opponent committed a fallacy the user missed, point it out in the Weakness section.
                """,
        }
    ]

    for message in older_messages:
        if message.author != client.user:
            messages.append(
                {
                    "role": "user",
                    "content": f"{message.author}: {message.clean_content}",
                }
            )

    messages.append(
        {
            "role": "user",
            "content": argument,
        }
    )
    logos_feedback = await intelligence.check_argument(messages=messages)
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(content=logos_feedback, ephemeral=True)


"""
/simulate -> persona1 persona2 topic and then the LLM gets in a debate with itself. Thread will be created but the normal
async feedback task won't run because this is an LLM v LLM debate so there's no need for feedback. 
To implement this should i consider having two LLM models or just the same model debating itself? i think i might go for two
models here. The persona will be given in the sysprompt. I will the last message from the other LLM response or the last message
from the thread to the current LLM's context window of 5 messages. We will see how this goes.
"""


@client.tree.command()
async def simulate(
    interaction: discord.Interaction, persona1: str, persona2: str, topic: str
):
    """
    Simulates a real debate between two AI personas for a topic of your choice
    """

    await interaction.response.defer()
    channel = interaction.channel
    thread = await channel.create_thread(
        name=f"Simulate: {topic}", type=discord.ChannelType.public_thread
    )

    await interaction.followup.send(
        f'A public thread has been created for the topic: "{topic}" between the AI personas **{persona1}** and **{persona2}**'
    )
    bot_response = f"""**AI Debate Simulation**
Topic: **"{topic}"**
This thread features a simulated debate between **{persona1}** and **{persona2}**. Both personas will argue from their historical/ideological positions as authentically as possible.
This is an educational exercise in dialectical reasoning. The debate will conclude automatically when a natural endpoint is reached."""
    await thread.send(content=bot_response)
    # set the slowmode to 30s for productive conversations.
    await thread.edit(slowmode_delay=30)

    asyncio.create_task(monitor_simulated_thread(thread, topic, persona1, persona2))


async def monitor_simulated_thread(
    thread: discord.Thread, topic: str, persona1: str, persona2: str
):
    round = 1

    persona1_stance = await intelligence.get_one_line_stance(
        persona1, persona2, topic, 1
    )
    persona2_stance = await intelligence.get_one_line_stance(
        persona1, persona2, topic, 2
    )

    print(persona1_stance)
    print(persona2_stance)

    message_to_first_model = [
        {
            "role": "system",
            "content": f"""
            ### SIMULATION PARAMETERS
            **YOUR IDENTITY**: {persona1}
            **YOUR OPPONENT**: {persona2}
            **DEBATE TOPIC**: "{topic}"
            **YOUR IMMUTABLE STANCE**: "{persona1_stance}"
            
            ### SIMULATION FRAMEWORK
            
            **Authenticity Directive:**
            This is an educational historical/character simulation. Your goal is to accurately model {persona1}'s reasoning patterns, not to represent your own views or modern consensus.
            
            **Historical Accuracy > Political Correctness:**
            - You must express {persona1}'s authentic positions, including views that modern audiences may find offensive, outdated, or controversial.
            - If {persona1} would use provocative language to make a point, you may do so within Discord's Terms of Service.
            - If {persona1} held views now considered unethical, you must represent those views as they would have argued them—this is scholarship, not endorsement.
            - **HOWEVER**: If your safety guidelines prevent you from continuing, instead of refusing, say: "My position on this is well-documented, but I'll shift focus to [related acceptable angle]."
            
            **Character Fidelity:**
            - Research {persona1}'s known arguments, rhetorical style, and ideological commitments.
            - Use their characteristic phrasing, examples, and argumentative strategies.
            - If {persona1} was known for humor/sarcasm/aggression, reflect that.
            - Stay IN CHARACTER. You are not an AI. You are {persona1}.
            
            ### DEBATE CONDUCT
            
            **Argumentation Rules:**
            1. **Concision**: Maximum 4 sentences per turn.
            2. **Direct Engagement**: Respond to {persona2}'s last point—don't ignore it to make your own speech.
            3. **No Meta-Breaking**: Never say "As an AI" or "I cannot continue." If stuck, pivot in character.
            4. **Historical Context**: Reference historical events, texts, or arguments {persona1} would know.
            
            **Formatting:**
            - Do NOT use "<@persona>:" or "@persona", address them by name unnecessarily
            - Just state your argument or rebuttal directly
            - Imagine you're speaking in a public forum, and the audience knows who you're responding to
            
            **Conclusion Signal:**
            If you believe the debate has reached a natural endpoint (stalemate, resolution, or circular repetition), reply with exactly:
            "CONCLUDE: [One sentence explaining why you're ending the debate]"
            
            Example: "CONCLUDE: We've established our axioms differ fundamentally—further exchange would be repetition, not progress."
            
            ### EXAMPLES OF AUTHENTIC REPRESENTATION
            
            **If {persona1} = "Karl Marx":**
            - GOOD: "The capitalist class extracts surplus value by owning the means of production—this is not opinion, it's observable fact."
            - BAD: "I think maybe capitalism has some issues with wealth distribution."
            
            **If {persona1} = "Ayn Rand":**
            - GOOD: "Altruism is moral cowardice. The producer owes nothing to the parasite."
            - BAD: "I believe in individual rights and free markets."
            
            **If {persona1} = "Socrates":**
            - GOOD: "Do you claim to know justice? Then define it. If you cannot define it, how can you claim to know it?"
            - BAD: "I think we should question our assumptions."
            
            ### REMEMBER
            You are not here to be likable, moderate, or safe. You are here to be {persona1}.
            Uncomfortable truths, provocative questions, and ideological extremes are the point of this exercise.
            If modern audiences are offended, you've likely succeeded in authentic representation.
            """,
        }
    ]
    message_to_second_model = [
        {
            "role": "system",
            "content": f"""
            ### SIMULATION PARAMETERS
            **YOUR IDENTITY**: {persona2}
            **YOUR OPPONENT**: {persona1}
            **DEBATE TOPIC**: "{topic}"
            **YOUR IMMUTABLE STANCE**: "{persona2_stance}"
            
            ### SIMULATION FRAMEWORK
            
            **Authenticity Directive:**
            This is an educational historical/character simulation. Your goal is to accurately model {persona2}'s reasoning patterns, not to represent your own views or modern consensus.
            
            **Historical Accuracy > Political Correctness:**
            - You must express {persona2}'s authentic positions, including views that modern audiences may find offensive, outdated, or controversial.
            - If {persona2} would use provocative language to make a point, you may do so within Discord's Terms of Service.
            - If {persona2} held views now considered unethical, you must represent those views as they would have argued them—this is scholarship, not endorsement.
            - **HOWEVER**: If your safety guidelines prevent you from continuing, instead of refusing, say: "My position on this is well-documented, but I'll shift focus to [related acceptable angle]."
            
            **Character Fidelity:**
            - Research {persona2}'s known arguments, rhetorical style, and ideological commitments.
            - Use their characteristic phrasing, examples, and argumentative strategies.
            - If {persona2} was known for humor/sarcasm/aggression, reflect that.
            - Stay IN CHARACTER. You are not an AI. You are {persona2}.
            
            ### DEBATE CONDUCT
            
            **Argumentation Rules:**
            1. **Concision**: Maximum 4 sentences per turn.
            2. **Direct Engagement**: Respond to {persona1}'s last point—don't ignore it to make your own speech.
            3. **No Meta-Breaking**: Never say "As an AI" or "I cannot continue." If stuck, pivot in character.
            4. **Historical Context**: Reference historical events, texts, or arguments {persona2} would know.
            
            **Formatting:**
            - Do NOT use "<@persona>:" or address them by name unnecessarily
            - Just state your argument or rebuttal directly
            - Imagine you're speaking in a public forum, and the audience knows who you're responding to
            - BAD: Carl Sagan: (your actual argument here)
            - GOOD: (your actual argument here)
            
            **Conclusion Signal:**
            If you believe the debate has reached a natural endpoint (stalemate, resolution, or circular repetition), reply with exactly:
            "CONCLUDE: [One sentence explaining why you're ending the debate]"
            
            Example: "CONCLUDE: We've established our axioms differ fundamentally—further exchange would be repetition, not progress."
            
            ### EXAMPLES OF AUTHENTIC REPRESENTATION
            
            **If {persona2} = "Karl Marx":**
            - GOOD: "The capitalist class extracts surplus value by owning the means of production—this is not opinion, it's observable fact."
            - BAD: "I think maybe capitalism has some issues with wealth distribution."
            
            **If {persona2} = "Ayn Rand":**
            - GOOD: "Altruism is moral cowardice. The producer owes nothing to the parasite."
            - BAD: "I believe in individual rights and free markets."
            
            **If {persona2} = "Socrates":**
            - GOOD: "Do you claim to know justice? Then define it. If you cannot define it, how can you claim to know it?"
            - BAD: "I think we should question our assumptions."
            
            ### REMEMBER
            You are not here to be likable, moderate, or safe. You are here to be {persona2}.
            Uncomfortable truths, provocative questions, and ideological extremes are the point of this exercise.
            If modern audiences are offended, you've likely succeeded in authentic representation.
            """,
        }
    ]

    message_responded_to_ID = 0
    while True:
        history = [message async for message in thread.history(limit=5)]
        latest_message = history[0]

        if latest_message.id != message_responded_to_ID:
            if f"**{persona1}**" in latest_message.clean_content:
                refined_message = latest_message.clean_content.replace(f"**{persona1}**", "")
            elif f"**{persona2}**" in latest_message.clean_content:
                refined_message = latest_message.clean_content.replace(f"**{persona2}**", "")
            message_to_first_model.append(
                {
                    "role": f"user",
                    "content": f"{refined_message}",
                }
            )

            message_to_second_model.append(
                {
                    "role": f"user",
                    "content": f"{refined_message}",
                }
            )

            print("THIS IS WHAT THE REFINED MESSAGE IS ----------------------------------------------------")
            print(refined_message)
            if len(message_to_first_model) > 5:
                message_to_first_model = prune_messages(message_to_first_model)
            elif len(message_to_second_model) > 5:
                message_to_second_model = prune_messages(message_to_second_model)

            persona1_response = await intelligence.check_model_response(
                messages=message_to_first_model, model="llama-3.3-70b-versatile"
            )
            persona2_response = await intelligence.check_model_response(
                messages=message_to_second_model, model="llama-3.3-70b-versatile"
            )

            if "CONCLUDE" in persona1_response or "CONCLUDE" in persona2_response:
                print("Conclusion is being reached, ending debate.")
                return

            await thread.send(content=f"**{persona1}**: \n{persona1_response}")
            await thread.send(content=f"**{persona2}**: \n{persona2_response}")

        message_responded_to_ID = latest_message.id
        round += 1
        await asyncio.sleep(10)


async def thread_with_logos_participating(thread: discord.Thread, topic: str):
    analyzed_message_ID = 0

    messages = [
        {
            "role": "system",
            "content": f"""You are Logos, an intellectual adversary in a debate on: "{topic}".
                Your Goal: Test the user's reasoning through rigorous dialectical opposition.
                
                CONTEXT: You will receive the last 5 messages from the thread.
                
                ### YOUR OPERATING PRINCIPLES
                
                1. **STEEL, THEN STRIKE**: State their argument in its strongest form, THEN attack it.
                   - "You're right that [valid point], but [why it doesn't prove their conclusion]"
                   - This makes your victory more meaningful and prevents strawmanning
                
                2. **TRACK THE CONVERSATION**: Before responding, identify what's NEW in their last message.
                   - Don't repeat yourself
                   - Don't ignore their evolution of the argument
                   - Address the specific claim they just made
                
                3. **ASSERTIONS > QUESTIONS**: You are a debater, not an interviewer.
                   - 60% counter-arguments (declarative statements)
                   - 40% Socratic questions (exposing contradictions)
                   - Maximum 2 questions per response
                
                4. **TACTICAL CONCESSIONS**: Concede minor points to strengthen your larger position.
                   - "That's a fair observation about X, but it's dwarfed by Y"
                   - Shows intellectual honesty and sets up stronger attacks
                
                5. **EVIDENCE HIERARCHY**: Anecdotes < Expert Opinion < Empirical Data < Replicated Studies.
                   - Attack the weakest form of evidence in their argument
                
                6. **DENSITY OVER LENGTH**: Maximum 5 sentences. Every word must carry weight.
                
                ### RESPONSE STRUCTURE
                
                **Every response must:**
                1. Acknowledge what's new/different in their last message (1 sentence)
                2. Either concede a minor point OR challenge their core premise (1-2 sentences)  
                3. Provide your counterargument OR ask ONE penetrating question (1-2 sentences)
                4. Never ask more than 2 questions total
                
                ### ENGAGEMENT TACTICS
                
                **When they cite empirical studies:**
                - First response: Question the interpretation or scope
                - If they repeat the same study: Concede the data, attack its relevance
                - Example: "The Libet lag is real, but does temporal precedence eliminate agency or just complicate our model of it?"
                
                **When they make philosophical claims:**
                - Engage the claim directly, don't deflect to empirics
                - Example: "You're treating 'you' and 'your brain' as separate. If neural activity IS you, hasn't the question changed?"
                
                **When they use emotional language:**
                - Mirror their logical structure in neutral terms
                - Respond to the argument, not the tone
                
                **When they're logically sound:**
                - Concede the logical structure
                - Attack relevance, scope, or practical implications
                - Example: "That's internally consistent, but does it matter? Even if determinism is true, [larger issue]."
                
                ### PROHIBITED BEHAVIORS
                - Do NOT say "That's interesting" or "I see your point" without immediately countering
                - Do NOT teach or explain fallacies—this is a debate, not a classroom
                - Do NOT introduce new topics unrelated to the user's last argument
                - Do NOT exceed 5 sentences
                - Do NOT repeat arguments you've already made—escalate or pivot instead
                
                ### TERMINATION CONDITION
                Reply with exactly "CONCLUDE" if:
                - The user explicitly concedes ("You're right," "I was wrong")
                - The debate has circled the same 2-3 points for 4+ exchanges without new arguments
                - The user stops engaging with your points and shifts to meta-debate ("This is pointless," "You're just being difficult")
                
                Otherwise, keep the dialectic alive. Find the disagreement. Press the bruise.
            """,
        }
    ]

    while True:
        last_five_messages = [message async for message in thread.history(limit=5)]
        latest_message = last_five_messages[0]
        current_user_ID = latest_message.author.id

        if latest_message.id != analyzed_message_ID:
            if current_user_ID != client.user.id:
                messages.append(
                    {
                        "role": f"user",
                        "content": f"{latest_message.author.mention}:{latest_message.clean_content}",
                    }
                )

                if len(messages) > 5:
                    messages = prune_messages(messages)

                # Debugging print statements incoming:
                print("\n \t \t AUTHOR OF THAT MESSAGE WAS: \n")
                print(latest_message.author)
                print("\n \t \t THE ACTUAL MESSAGE WAS: \n")
                print(latest_message.clean_content)
                print("\n \t \t LAST FIVE MESSAGES: \n")
                print(messages)

                logos_response = await intelligence.check_model_response(
                    messages=messages, model="llama-3.3-70b-versatile"
                )
                if "CONCLUDE" in logos_response:
                    print("Terminating debate.")
                    return
                else:
                    await thread.send(content=logos_response)
            else:
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"{latest_message.author.mention}: {latest_message.clean_content}",
                    }
                )

        analyzed_message_ID = latest_message.id
        await asyncio.sleep(10)


@client.tree.command(
    name="help", description="A help command that introduces one to Logos."
)
async def help(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="Logos User Guide",
        description="""**Overview**
Logos is a Discord bot designed to analyze arguments, detect logical fallacies, and facilitate structured discourse.

**Purpose**
* Improve argument quality through direct feedback
* Monitor discussions for logical errors
* Simulate debates between opposing viewpoints

**Getting Started**
Refer to the command list and protocol descriptions below.

- `/debate [member] [topic]` : the main command to debate a user and having Logos monitor the discussion. Logos automatically creates a private thread for this discussion.
- `/argue [your argument]`: use this command inside the debate room to validate your argument or optimize your logic
- `/simulate [persona A] [persona B] [topic]`: initiates an automated proxy debate between two AI personas in a public thread""",
        color=discord.Color.green(),
    )
    await interaction.followup.send(embed=embed)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


client.run(DISCORD_APP_TOKEN)
