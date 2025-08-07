from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings.
    """
    model_name: str = "meta-llama/Llama-3.2-1B"
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.90
    model_cache_dir: str = "/CACHE/MODELS"

settings = Settings() 