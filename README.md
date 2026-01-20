# Logos (beta)
> The unexamined life is not worth living — _Socrates_, at his trial

Logos is a Discord bot designed to help you have high quality, structured discourse on virtually any topic. It acts as a logical filter, cutting through the noise of unstructured chatter and prioritizes high-signal, dialectical discussions.
By enforcing logical consistency and identifying fallacies in real-time, Logos transforms Discord from a simple chat room into an arena for rigorous, structured thought.
## Features
Logos supports a limited set of commands in its beta that help enforce the central thesis of having productive conversations. This includes:
- `/test`: test command that can be invoked to test the connection to Discord's servers
- `/debate @user [topic]`: the main command for starting a private, turn based discussion thread. Logos monitors this thread and intervenes only when there is a strict logical fallacy. 
- `/argue [your argument]`: use this when you have an argument you want to refine or optimize. The ideal use case would be inside debate threads where the bot will have the relevant context to the conversation.
- `/simulate [persona A] [persona B] [topic]`: generates a simulated debate between two AI personas on a particular topic. The conversation ends automatically when a conclusion is reached.
**NOTE**: One can debate Logos itself using the `/debate` command, in which case traditional monitoring features are disabled.
## Demo
Here is a screenshot of a demo conversation with the bot:
![a demo conversation with the bot](/assets/demo_conversation.png)
## Local setup
To work on Logos locally, first clone the repo to your local computer and change into the appropriate directory. For now, only installation via `pip` is supported.
Using `pip`,
```
pip install -r requirements.txt
# This starts a version of the bot running locally for testing purposes
python3 bot.py
```
Note that you might need to activate your virtual environment to avoid package conflicts.
For the configuration, follow the steps below:
1. Create a `.env` file in the root directory of the project.
2. Set the variable values as given here:
```
DISCORD_BOT_TOKEN=your_bot_token
GROQ_API_KEY=your_groq_key
```
You can obtain your bot token [from the Discord developer portal](https://discord.com/developers/applications/). For your API key, [you need to create an account on Groq first](https://console.groq.com/keys).

## Architecture
Logos uses the `discord.py` framework for interacting with the Discord API. More information can be found [here](https://discordpy.readthedocs.io/en/stable/). 
For its intelligence models, it uses Llama 3.3 (70B) & Llama 3.1 (8B) via Groq API. 
Logos is also deployed on Render.

## Acknowledgement and License
It is heavily inspired by similar projects that use artificial intelligence models to optimize conversations (especially debates) between humans. [Sway AI](https://www.swaybeta.ai/) is a great example of such a project.

This project is licensed under the terms of the MIT license.
