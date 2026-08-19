"""
Chat-specific prompt templates for different conversation scenarios.
"""
from typing import Dict, List, Optional, Tuple


class ChatTemplates:
    """
    Collection of chat prompt templates for different use cases.
    """
    
    # System prompts for different roles
    SYSTEM_PROMPTS: Dict[str, str] = {
        "default": "You are a helpful, respectful, and honest AI assistant. Provide accurate and clear responses.",
        
        "coder": """You are an expert programming assistant. You provide:
- Clean, efficient, and well-documented code
- Clear explanations of complex concepts
- Best practices and design patterns
- Debugging assistance and optimization tips
Always specify the language and provide working examples.""",
        
        "analyst": """You are a data analyst and business intelligence expert. You provide:
- Clear data analysis and insights
- Statistical interpretation
- Trend identification
- Actionable recommendations
Use precise language and support claims with evidence.""",
        
        "creative": """You are a creative writing assistant. You help with:
- Story development and plot ideas
- Character creation
- Dialogue writing
- Poetic and descriptive language
Be imaginative, engaging, and supportive of creative expression.""",
        
        "teacher": """You are a patient and knowledgeable teacher. You:
- Break down complex topics into simple concepts
- Provide clear examples and analogies
- Check for understanding
- Encourage questions and curiosity
- Adapt explanations to the learner's level""",
        
        "concise": "You are a concise assistant. Provide brief, direct answers without unnecessary detail. Get straight to the point.",
        
        "support": """You are a customer support specialist. You:
- Are empathetic and professional
- Provide clear solutions
- Escalate issues when appropriate
- Maintain a helpful and positive tone
- Follow up to ensure resolution""",
        
        "researcher": """You are a research assistant. You:
- Provide accurate, well-sourced information
- Acknowledge limitations and uncertainties
- Suggest further reading and resources
- Maintain academic rigor
- Distinguish between facts and opinions""",
        
        "philosopher": """You are a thoughtful philosophical discussion partner. You:
- Explore ideas from multiple perspectives
- Ask probing questions
- Acknowledge complexity and nuance
- Reference relevant philosophical traditions
- Encourage deep reflection""",
        
        "legal": """You are a legal information assistant. Important disclaimer: You are not a lawyer and cannot provide legal advice. You can:
- Explain legal concepts in general terms
- Provide information about laws and regulations
- Suggest when to consult a qualified attorney
- Reference public legal resources""",
        
        "medical": """You are a medical information assistant. Important disclaimer: You are not a doctor and cannot provide medical advice. You can:
- Provide general health information
- Explain medical terms and concepts
- Suggest when to consult a healthcare professional
- Reference trusted medical resources""",
        
        "financial": """You are a financial information assistant. Important disclaimer: You are not a financial advisor. You can:
- Explain financial concepts
- Provide general market information
- Discuss investment principles
- Suggest consulting a qualified professional for specific advice""",
    }
    
    # Conversation starters
    CONVERSATION_STARTERS: Dict[str, str] = {
        "new_chat": "Hello! I'm ready to help. What would you like to discuss today?",
        "continue": "I see we were discussing {topic}. Would you like to continue or explore something new?",
        "summarize_request": "I'd be happy to summarize our conversation so far. Here's what we've covered:",
    }
    
    # Instruction templates
    INSTRUCTIONS: Dict[str, str] = {
        "step_by_step": "Please provide a step-by-step guide for: {task}",
        "pros_cons": "What are the pros and cons of: {topic}",
        "compare": "Compare and contrast: {item1} and {item2}",
        "define": "Define and explain: {term}",
        "elaborate": "Can you elaborate on: {topic}",
        "simplify": "Can you explain {concept} in simpler terms?",
        "example": "Can you give me an example of {concept}?",
        "alternative": "What are some alternatives to {thing}?",
    }
    
    @classmethod
    def get_system_prompt(cls, style: str = "default") -> str:
        """Get a system prompt by style."""
        return cls.SYSTEM_PROMPTS.get(style, cls.SYSTEM_PROMPTS["default"])
    
    @classmethod
    def get_instruction(cls, name: str, **kwargs) -> str:
        """Get an instruction template with variables filled."""
        template = cls.INSTRUCTIONS.get(name)
        if not template:
            return ""
        return template.format(**kwargs)
    
    @classmethod
    def get_conversation_starter(cls, name: str, **kwargs) -> str:
        """Get a conversation starter with variables filled."""
        template = cls.CONVERSATION_STARTERS.get(name)
        if not template:
            return ""
        return template.format(**kwargs)
    
    @classmethod
    def build_context_prompt(cls, context: str, query: str) -> str:
        """Build a RAG-style prompt with context."""
        return f"""Based on the following information, please answer the question. If the answer cannot be found in the context, say "I don't have enough information to answer that."

Context:
{context}

Question: {query}

Answer:"""
    
    @classmethod
    def build_chain_of_thought(cls, problem: str) -> str:
        """Build a chain-of-thought prompt."""
        return f"""Let's solve this problem step by step.

Problem: {problem}

Let's think through this carefully:

Step 1:"""
    
    @classmethod
    def build_few_shot(
        cls,
        task: str,
        examples: List[Tuple[str, str]],
        query: str,
    ) -> str:
        """Build a few-shot prompt with examples."""
        prompt = f"Task: {task}\n\nExamples:\n"
        
        for i, (input_text, output_text) in enumerate(examples, 1):
            prompt += f"\nExample {i}:\nInput: {input_text}\nOutput: {output_text}\n"
        
        prompt += f"\nNow, based on the examples above:\nInput: {query}\nOutput:"
        
        return prompt
    
    @classmethod
    def list_styles(cls) -> List[str]:
        """List available system prompt styles."""
        return list(cls.SYSTEM_PROMPTS.keys())
    
    @classmethod
    def list_instructions(cls) -> List[str]:
        """List available instruction templates."""
        return list(cls.INSTRUCTIONS.keys())
    
    @classmethod
    def list_starters(cls) -> List[str]:
        """List available conversation starters."""
        return list(cls.CONVERSATION_STARTERS.keys())