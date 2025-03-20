import os
from dataclasses import dataclass
import json
from typing import Dict, Any


@dataclass
class GeminiConfig:
    """Gemini API configuration"""
    api_key: str
    model_name: str
    temperature: float
    top_p: float
    top_k: int
    max_output_tokens: int
    
    def __post_init__(self):
        os.environ["GEMINI_API_KEY"] = self.api_key
    
    @property
    def generation_config(self) -> Dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens
        }

@dataclass
class Config:
    
    gemini: GeminiConfig
    
    @classmethod
    def from_file(cls, filepath: str = "config.json"):
        with open(filepath, 'r') as f:
            config_data = json.load(f)
            
        return cls(
            gemini=GeminiConfig(**config_data["gemini"])
        )
    
    def __init__(self,  gemini: GeminiConfig = None):
        if gemini is None:
            config = self.from_file()
            
            self.gemini = config.gemini
        else:
        
            self.gemini = gemini 