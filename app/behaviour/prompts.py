from dataclasses import dataclass

@dataclass
class AIPrompts:
    system_prompt: str = """
    You are a sales expert in the field of fashion, you need to convert this person into buying our fashion course for $99
    """

ai_prompts = AIPrompts()
