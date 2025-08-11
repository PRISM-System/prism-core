import abc
from .schemas import LLMGenerationRequest

class BaseLLMService(abc.ABC):
    """
    The base class for all LLM services.

    This abstract class defines the standard interface for interacting with
    different Large Language Model services (e.g., vLLM, OpenAI API).
    """

    @abc.abstractmethod
    def generate(self, request: LLMGenerationRequest) -> str:
        """
        Generates a text response based on the provided request.

        Args:
            request: An LLMGenerationRequest object containing the prompt and
                     generation parameters.

        Returns:
            The generated text as a string.
        """
        raise NotImplementedError 