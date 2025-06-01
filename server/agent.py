# agent.py
def agent_executor():
    return {
        "invoke": lambda input: f"Echo response for: {input['input']}"
    }

# Or if agent_executor is just a function, not an object:
def invoke(input):
    return f"Echo response for: {input['input']}"
