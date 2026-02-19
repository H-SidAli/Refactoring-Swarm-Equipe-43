"""
Base Agent Class - Foundation for all Refactoring Swarm agents.
All agents MUST inherit from this class to ensure IGL compliance.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional
from langchain_openai import ChatOpenAI
from src.utils.logger import log_experiment, ActionType


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Refactoring Swarm.
    Ensures consistent LLM interaction and mandatory logging.
    """

    def __init__(self, name: str, model_name: str = "mistral-small-latest"):
        """
        Initialize the base agent.

        Args:
            name (str): Agent identifier (e.g., "Auditor", "Fixer").
            model_name (str): Google Gemini model to use.
        """
        self.name = name
        self.model_name = model_name
        self._llm: Optional[ChatOpenAI] = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy initialization of the LLM client."""
        if self._llm is None:
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError(
                    "❌ MISTRAL_API_KEY non définie. "
                    "Vérifiez votre fichier .env"
                )

            # Allow overriding base URL to point to self-hosted/proxy endpoints if needed.
            base_url = os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai/v1")

            self._llm = ChatOpenAI(
                model=self.model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2
            )
        return self._llm

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_action_type(self) -> ActionType:
        """Return the ActionType for logging purposes."""
        pass

    def invoke(self, input_prompt: str) -> str:
        """
        Execute the agent with mandatory logging.
        
        This method ensures ALL LLM interactions are logged
        per IGL Technical Configuration Guide.
        Includes rate limit handling with exponential backoff.

        Args:
            input_prompt (str): The user/system prompt to process.

        Returns:
            str: The LLM response.
        """
        # Build messages
        messages = [
            ("system", self.get_system_prompt()),
            ("human", input_prompt)
        ]

        # Call LLM with rate limit handling
        max_retries = 3
        retry_count = 0
        output_response = None
        status = "FAILURE"

        while retry_count < max_retries:
            try:
                response = self.llm.invoke(messages)
                output_response = response.content
                status = "SUCCESS"
                break
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limit error (429)
                if "429" in error_msg or "quota" in error_msg.lower():
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff: 2^retry_count seconds
                        wait_time = 2 ** retry_count
                        print(f"⏸️  Rate limit hit. Retrying in {wait_time}s (attempt {retry_count}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # Other errors: don't retry
                output_response = f"ERROR: {error_msg}"
                status = "FAILURE"
                break

        # MANDATORY LOGGING - IGL Compliance
        log_experiment(
            agent_name=self.name,
            model_used=self.model_name,
            action=self.get_action_type(),
            details={
                "input_prompt": input_prompt,
                "output_response": output_response
            },
            status=status
        )

        if status == "FAILURE":
            raise RuntimeError(output_response)

        return output_response

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, model={self.model_name})>"
