from vllm import LLM, SamplingParams
from .config import settings
from .schemas import LLMGenerationRequest

class LLMService:
    def __init__(self):
        self.llm = LLM(
            model=settings.model_name,
            tensor_parallel_size=settings.tensor_parallel_size,
            gpu_memory_utilization=settings.gpu_memory_utilization,
            download_dir=settings.model_cache_dir,
        )

    def generate(self, request: LLMGenerationRequest):
        sampling_params = SamplingParams(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        outputs = self.llm.generate(request.prompt, sampling_params)
        return outputs[0].outputs[0].text

llm_service = LLMService() 