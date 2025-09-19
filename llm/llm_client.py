import os
import time
import json
import logging
import asyncio
from typing import Optional, Any, Dict

import openai
from pydantic import BaseModel, Field, validator
from openai import AsyncOpenAI

from . import tools
from . import prompts
from logs_management.log_manager import log_error, log_performance, get_correlation_id

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration for LLM client."""
    api_key: str = Field(..., description="OpenAI API key")
    base_url: str = Field(default="https://api.openai.com/v1", description="API base URL")
    model: str = Field(default="gpt-3.5-turbo", description="Model name")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Temperature for generation")
    timeout: int = Field(default=100, ge=10, le=300, description="Request timeout in seconds")
    max_function_calls: int = Field(default=10, ge=1, le=20, description="Maximum function calls per request")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        if not v.startswith(('sk-', 'sess-')):
            logger.warning("API key doesn't match expected format")
        return v.strip()

def get_llm_config() -> LLMConfig:
    """Get LLM configuration from environment variables."""
    try:
        # Type conversion helpers
        def get_int_env(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, default))
            except (ValueError, TypeError):
                logger.warning(f"Invalid integer value for {key}, using default: {default}")
                return default
                
        def get_float_env(key: str, default: float) -> float:
            try:
                return float(os.getenv(key, default))
            except (ValueError, TypeError):
                logger.warning(f"Invalid float value for {key}, using default: {default}")
                return default
        
        config = LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            max_retries=get_int_env("OPENAI_MAX_RETRIES", 3),
            temperature=get_float_env("OPENAI_TEMPERATURE", 0.3),
            timeout=get_int_env("OPENAI_TIMEOUT", 100),
            max_function_calls=get_int_env("OPENAI_MAX_FUNCTION_CALLS", 10)
        )
        
        logger.info(f"LLM configuration loaded: model={config.model}, timeout={config.timeout}s")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load LLM configuration: {str(e)}")
        raise RuntimeError(f"LLM configuration error: {str(e)}") from e


class LLMClient:
    """Async LLM client with error handling and logging."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client with configuration."""
        try:
            self.llm_config = config or get_llm_config()
            
            self.client = AsyncOpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
                timeout=self.llm_config.timeout,
                max_retries=0  # We handle retries manually
            )
            
            logger.info("LLM Client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            raise RuntimeError(f"LLM client initialization failed: {str(e)}") from e
        
    async def process_query(self, user_query: str, error_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user query with LLM and function calling.
        
        Args:
            user_query: User's query text
            error_feedback: Optional feedback from previous errors
            
        Returns:
            Dict containing the LLM response
            
        Raises:
            RuntimeError: If processing fails
        """
        if not user_query or not user_query.strip():
            raise ValueError("User query cannot be empty")
            
        start_time = time.time()
        correlation_id = get_correlation_id()
        
        logger.info(
            f"Processing query with LLM",
            extra={'extra_data': {
                'query_length': len(user_query),
                'has_error_feedback': bool(error_feedback),
                'model': self.llm_config.model,
                'correlation_id': correlation_id
            }}
        )
        
        try:
            # Prepare system prompt
            system_prompt = prompts.create_system_prompt_mindmap_query()
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add user message with optional error feedback
            if error_feedback:
                user_content = (
                    f"Previous response had errors: {error_feedback}. "
                    f"Please fix and provide a corrected response for: {user_query}"
                )
                logger.info(f"Including error feedback in request")
            else:
                user_content = user_query
                
            messages.append({'role': 'user', 'content': user_content})

            function_calls_made = []
            max_function_calls = self.llm_config.max_function_calls
            
            for call_iteration in range(max_function_calls):
                logger.debug(
                    f"Function call iteration {call_iteration + 1}/{max_function_calls}",
                    extra={'extra_data': {
                        'iteration': call_iteration + 1,
                        'correlation_id': correlation_id
                    }}
                )
                
                try:
                    # Make API call
                    response = await self._make_api_call(messages)
                    
                    if not response or not response.choices:
                        raise RuntimeError("Empty or invalid response from API")
                        
                    message = response.choices[0].message
                    
                    # Check if LLM wants to call a function
                    if hasattr(message, 'function_call') and message.function_call:
                        function_name = message.function_call.name
                        
                        try:
                            function_args = json.loads(message.function_call.arguments)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid function arguments JSON: {str(e)}")
                            raise RuntimeError(f"Invalid function call arguments: {str(e)}")
                        
                        logger.info(
                            f"Executing function call: {function_name}",
                            extra={'extra_data': {
                                'function_name': function_name,
                                'iteration': call_iteration + 1,
                                'correlation_id': correlation_id
                            }}
                        )
                        
                        # Execute the function
                        try:
                            function_result = tools.execute_function_call(function_name, function_args)
                        except Exception as e:
                            logger.error(f"Function execution failed: {str(e)}")
                            function_result = f"Function execution error: {str(e)}"
                        
                        # Store the function call
                        function_calls_made.append({
                            "function": function_name,
                            "parameters": function_args,
                            "result": function_result
                        })
                        
                        # Add assistant's function call to conversation
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "function_call": message.function_call
                        })
                        
                        # Add function result to conversation
                        messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": str(function_result)
                        })
                        
                        # Continue the loop to see if LLM wants to call another function
                        continue
                        
                    else:
                        # No function call, we have the final response
                        final_content = message.content
                        break
                        
                except openai.APIError as e:
                    logger.error(f"OpenAI API error on iteration {call_iteration + 1}: {str(e)}")
                    if call_iteration == max_function_calls - 1:
                        raise RuntimeError(f"API error: {str(e)}")
                    continue
                    
            else:
                # If we exit the loop without breaking (hit max function calls)
                logger.warning(f"Hit maximum function calls ({max_function_calls}), getting final response")
                
                try:
                    final_messages = messages + [{
                        "role": "user", 
                        "content": "Please provide your final response based on the function calls you've made."
                    }]
                    
                    final_response = await self._make_api_call(final_messages, use_functions=False)
                    
                    if final_response and final_response.choices:
                        final_content = final_response.choices[0].message.content
                    else:
                        raise RuntimeError("Failed to get final response after max function calls")
                        
                except Exception as e:
                    logger.error(f"Failed to get final response: {str(e)}")
                    raise RuntimeError(f"Failed to get final response after {max_function_calls} function calls")

            # Parse and return the response
            end_time = time.time()
            
            try:
                response_json = json.loads(final_content) if final_content else {}
                
                # Add function calls to response if they exist
                if function_calls_made:
                    response_json["function_calls"] = function_calls_made
                    
                log_performance(
                    logger,
                    "llm_processing",
                    start_time,
                    end_time,
                    function_calls=len(function_calls_made),
                    model=self.llm_config.model,
                    correlation_id=correlation_id
                )
                
                logger.info(f"Query processing completed with {len(function_calls_made)} function calls")
                return response_json
                
            except json.JSONDecodeError as e:
                logger.warning(f"Response not valid JSON, wrapping: {str(e)}")
                
                # If not JSON, wrap in expected format
                wrapped_response = {
                    "status": "success",
                    "data": {"response": final_content or "Empty response"},
                    "function_calls": function_calls_made,
                    "message": "Response generated successfully (non-JSON format)"
                }
                
                log_performance(
                    logger,
                    "llm_processing",
                    start_time,
                    end_time,
                    function_calls=len(function_calls_made),
                    model=self.llm_config.model,
                    json_parse_error=True,
                    correlation_id=correlation_id
                )
                
                return wrapped_response
                
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            end_time = time.time()
            log_error(logger, e, {
                'operation': 'llm_processing',
                'query_length': len(user_query),
                'processing_time': end_time - start_time,
                'model': self.llm_config.model,
                'correlation_id': correlation_id
            })
            raise RuntimeError(f"LLM processing failed: {str(e)}") from e
    
    async def _make_api_call(self, messages: list, use_functions: bool = True) -> Any:
        """
        Make API call with proper error handling and retries.
        
        Args:
            messages: Conversation messages
            use_functions: Whether to include function definitions
            
        Returns:
            API response
        """
        for attempt in range(self.llm_config.max_retries):
            try:
                call_params = {
                    'model': self.llm_config.model,
                    'temperature': self.llm_config.temperature,
                    'messages': messages
                }
                
                if use_functions:
                    call_params['functions'] = tools.define_functions()
                    call_params['function_call'] = "auto"
                
                response = await self.client.chat.completions.create(**call_params)
                return response
                
            except openai.RateLimitError as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {wait_time}s")
                if attempt < self.llm_config.max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(f"Rate limit exceeded after {self.llm_config.max_retries} attempts") from e
                
            except openai.APITimeoutError as e:
                logger.warning(f"API timeout on attempt {attempt + 1}")
                if attempt < self.llm_config.max_retries - 1:
                    continue
                raise RuntimeError(f"API timeout after {self.llm_config.max_retries} attempts") from e
                
            except openai.APIConnectionError as e:
                logger.warning(f"API connection error on attempt {attempt + 1}")
                if attempt < self.llm_config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise RuntimeError(f"API connection failed after {self.llm_config.max_retries} attempts") from e
                
            except openai.APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.llm_config.max_retries - 1 and e.status_code >= 500:
                    # Retry server errors
                    await asyncio.sleep(1)
                    continue
                raise RuntimeError(f"API error: {str(e)}") from e
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.llm_config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise RuntimeError(f"Unexpected API error: {str(e)}") from e
                
        raise RuntimeError("All API call attempts failed")
