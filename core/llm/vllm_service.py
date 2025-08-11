from vllm import LLM, SamplingParams
from ..config import settings
from ..schemas import LLMGenerationRequest
from .base import BaseLLMService

class VLLMService(BaseLLMService):
    """
    An LLM service implementation using the vLLM library.
    """
    def __init__(self):
        self.llm = LLM(
            model=settings.model_name,
            tensor_parallel_size=settings.tensor_parallel_size,
            gpu_memory_utilization=settings.gpu_memory_utilization,
            download_dir=settings.model_cache_dir,
        )

    def generate(self, request: LLMGenerationRequest) -> str:
        """
        Generates text using the vLLM engine.
        """
        sampling_params = SamplingParams(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        # vLLM's generate method returns a list of RequestOutput objects.
        # We access the first result's first output's text.
        outputs = self.llm.generate(request.prompt, sampling_params)
        return outputs[0].outputs[0].text 