"""
Prompt template manager for storing and rendering templates.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import re
from pathlib import Path
import json

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """A prompt template with variables and metadata."""
    
    name: str
    template: str
    description: str = ""
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None

    def __post_init__(self):
        if not self.variables:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variable names from template."""
        pattern = r"\{(\w+)\}"
        return list(set(re.findall(pattern, self.template)))

    def render(self, **kwargs) -> str:
        """Render template with provided variables."""
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable: {e}")

    def render_with_system(self, **kwargs) -> Dict[str, str]:
        """Render template with system prompt."""
        result = {}
        if self.system_prompt:
            if "{" in self.system_prompt:
                result["system"] = self.system_prompt.format(**kwargs)
            else:
                result["system"] = self.system_prompt
        result["user"] = self.render(**kwargs)
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags,
            "system_prompt": self.system_prompt,
            "example_input": self.example_input,
            "example_output": self.example_output,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            template=data["template"],
            description=data.get("description", ""),
            variables=data.get("variables", []),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            system_prompt=data.get("system_prompt"),
            example_input=data.get("example_input"),
            example_output=data.get("example_output"),
        )


class PromptTemplateManager:
    """Manager for prompt templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
        if templates_dir and templates_dir.exists():
            self.load_from_directory(templates_dir)

    def _load_builtin_templates(self):
        """Load built-in prompt templates."""
        templates_list = [
            PromptTemplate(
                name="summarize",
                template="""Please provide a concise summary of the following text. Focus on the key points and main ideas.

Text to summarize:
{text}

Summary:""",
                description="Summarize a long text into key points",
                category="text_processing",
                tags=["summary", "condense", "extract"],
            ),
            PromptTemplate(
                name="explain",
                template="""Explain the following concept in simple, easy-to-understand terms. Provide examples if helpful.

Concept: {concept}

Explanation:""",
                description="Explain a concept simply",
                category="education",
                tags=["explanation", "learning", "teaching"],
                system_prompt="You are a patient teacher who explains complex topics in simple terms.",
            ),
            PromptTemplate(
                name="analyze",
                template="""Analyze the following data and provide key insights, trends, and notable patterns.

Data:
{data}

Analysis:""",
                description="Analyze data and provide insights",
                category="analysis",
                tags=["data", "insights", "analytics"],
            ),
            PromptTemplate(
                name="code_review",
                template="""Review the following {language} code. Identify potential bugs, performance issues, and suggest improvements. Be specific and provide examples.

```{language}
{code}
Review:
""",
category="programming"
)
]
        for template in templates_list:
            self.templates[template.name] = template


def get(self, name):

    return self.templates.get(name)


def render(self, name, **kwargs):

    template = self.get(name)

    if template is None:
        raise ValueError("Template not found")

    return template.render(**kwargs)


def render_with_system(self, name, **kwargs):

    template = self.get(name)

    if template is None:
        raise ValueError("Template not found")

    return template.render_with_system(**kwargs)


def load_from_directory(self, directory: Path):

    loaded = 0

    # JSON loader
    for json_file in directory.glob("*.json"):

        try:

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):

                for item in data:
                    template = PromptTemplate.from_dict(item)
                    self.templates[template.name] = template
                    loaded += 1

            else:

                template = PromptTemplate.from_dict(data)
                self.templates[template.name] = template
                loaded += 1

        except Exception as e:

            logger.error(f"Error loading {json_file}: {e}")

    return loaded