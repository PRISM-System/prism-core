from vllm import LLM, SamplingParams
from .config import settings

class LLMService:
    def __init__(self):
        self.llm = LLM(
            model=settings.model_name,
            tensor_parallel_size=settings.tensor_parallel_size,
            gpu_memory_utilization=settings.gpu_memory_utilization,
            download_dir=settings.model_cache_dir,
        )

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, stop: list[str] = None):
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
        outputs = self.llm.generate(prompt, sampling_params)
        return outputs[0].outputs[0].text

llm_service = LLMService() 