"""
LLM Service - Ollama integration for personality generation and chat
"""
import logging
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM service wrapper using Ollama API.
    """
    
    def __init__(self, config=None):
        """
        Initialize LLM service with Ollama.
        
        Args:
            config: LLMConfig instance (optional)
        """
        if config is None:
            from config.llm_config import LLMConfig
            config = LLMConfig
        
        self.config = config
        self.use_ollama = False
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM using Ollama"""
        try:
            # Test Ollama connection
            response = requests.get(
                f"{self.config.OLLAMA_BASE_URL}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                self.use_ollama = True
                logger.info("Ollama API initialized successfully")
                logger.info(f"Using model: {self.config.OLLAMA_MODEL}")
                return
            else:
                logger.warning(f"Ollama returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Ollama not available: Connection refused")
            logger.info("Make sure Ollama is installed and running:")
            logger.info("  1. Install from https://ollama.ai")
            logger.info(f"  2. Run: ollama pull {self.config.OLLAMA_MODEL}")
            logger.info("  3. Ensure Ollama is running")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        
        # If Ollama fails, don't raise - let the app continue without LLM
        logger.warning(
            "Ollama LLM backend not available. LLM features will be disabled.\n"
            "To enable personality and chat features:\n"
            "  1. Install Ollama from https://ollama.ai\n"
            f"  2. Run: ollama pull {self.config.OLLAMA_MODEL}\n"
            "  3. Ensure Ollama is running and restart the application"
        )
        self.use_ollama = False
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from a prompt using Ollama.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (default from config)
            temperature: Sampling temperature (default from config)
            stop: Stop sequences (default: ["\n\n", "##"])
            
        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("Ollama LLM service is not available. Please install and run Ollama.")
        
        max_tokens = max_tokens or self.config.MAX_TOKENS
        temperature = temperature or self.config.TEMPERATURE
        stop = stop or ["\n\n", "##", "Task:"]
        
        return self._generate_ollama(prompt, max_tokens, temperature, stop)
    
    def _generate_ollama(self, prompt: str, max_tokens: int, temperature: float, stop: List[str]) -> str:
        """Generate using Ollama API"""
        try:
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": self.config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "stop": stop
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise RuntimeError(f"Failed to generate response from Ollama: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with Ollama: {e}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from prompt.
        Attempts to parse JSON from Ollama output.
        
        Args:
            prompt: Input prompt requesting JSON output
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON dictionary
        """
        import json
        
        # Add JSON format instruction to prompt
        json_prompt = prompt + "\n\nRespond with ONLY valid JSON, no additional text."
        
        response = self.generate(
            json_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["\n\n", "```"]
        )
        
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Ollama response: {e}")
            logger.warning(f"Response was: {response[:200]}")
            # Try to find JSON object in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse JSON from Ollama response: {response[:200]}")
    
    def is_available(self) -> bool:
        """Check if Ollama LLM service is available"""
        return self.use_ollama
