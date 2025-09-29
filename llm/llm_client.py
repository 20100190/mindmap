from typing import List
from pydantic import BaseModel
import openai
import os
from . import tools
import json
import asyncio
from . import schema
import jsonschema
from . import prompts
from typing import Optional, Any
from util.process_json_mindmap import normalize_llm_response, extract_first_json_chunk, validate_json_structure
from typing import Dict, Optional, Any
import logging
from chat_log_cache.chat_log import chat_logs_cache
logger = logging.getLogger(__name__)

class OutputResponse(BaseModel):
    main_response: Dict[str, Any] # ChatCompletionMessage.content
    function_calls:Optional[list]
    full_response: Any #ChatCompletion
    chat_log: List


class LLMConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    temperature: float = 0.3
    timeout: int = 100  # seconds
    max_function_calls: int=10

def get_llm_config() -> LLMConfig:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        logger.error("API key is missing.")
        raise ValueError("Missing API key.")
    return LLMConfig(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", 3)),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.3)),
        timeout=int(os.getenv("OPENAI_TIMEOUT", 100))
        )

class LLMClient:
    def __init__(self):
        self.llm_config = get_llm_config()
        self.client = openai.AsyncOpenAI(
            api_key=self.llm_config.api_key,
            base_url=self.llm_config.base_url,
            timeout=self.llm_config.timeout
        )
        
    async def _call_llm(self, message:list, tool_usage=True):
        """
        message: User message + history to pass to model
        return: LLM response : ChatCompletion
        """
        try:
            response = await self.client.chat.completions.create(
                        model=self.llm_config.model,
                        temperature=self.llm_config.temperature,
                        messages=message,
                        functions=tools.define_functions() if tool_usage else None,
                        function_call="auto" if tool_usage else None
                    )
            if not response.choices:
                logger.error("Empty Choice list")
                raise openai.APIStatusError("Empty choice list", response=response)
            return response  
        except openai.AuthenticationError as e:
            logger.error(f"Colud not authenticate with given API key. Error: {e}")
            raise
        except openai.RateLimitError as e:
            logger.error(f"Hitting rate limit. Error: {e}")
            raise
        except openai.APIStatusError as e:
            logger.error(f"Bad API response. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unknown Exception occured in API call. Error: {e}")
            raise
    
    def _handle_function_call(self, message):
        """
        Take ChatCompletionMessage Objetc and execute requested function call 
        message: ChatCompletionMessage
        return: function call and response to append in message, function call history
        """
        function_response =[]
        function_calls_executed = []
        function_name = message.function_call.name
        try:
            function_args = json.loads(message.function_call.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"Function parameters not Json compatible. Error: {e}")

            function_response.append({
                "role": "assistant",
                "content": None,
                "function_call": message.function_call
            })
            
            # Add function result to conversation
            function_response.append({
                "role": "function",
                "name": function_name,
                "content": f"Could not convert args to Json. Error: {e}. Please fix and try agian."
            })

            return function_response, function_calls_executed
        
        try:
            # Execute the function
            function_result = tools.execute_function_call(function_name, function_args)
        except Exception as e:
            logger.error(f"Fail to execute use tool. Error {e}")
            
            # Add assistant's function call to conversation
            function_response.append({
                "role": "assistant",
                "content": None,
                "function_call": message.function_call
            })
            
            # Add function result to conversation
            function_response.append({
                "role": "function",
                "name": function_name,
                "content": "Error in last function call: " + e + "Please fix and retry."
            })

            return function_response, function_calls_executed
        
        # Store the function call
        function_calls_executed.append({
            "function": function_name,
            "parameters": function_args,
            "result": function_result
        })
        
        # Add assistant's function call to conversation
        function_response.append({
            "role": "assistant",
            "content": None,
            "function_call": message.function_call.model_dump()
        })
        
        # Add function result to conversation
        function_response.append({
            "role": "function",
            "name": function_name,
            "content": function_result
        })

        return function_response, function_calls_executed

        
    async def process_query(self, user_request, error_feedback: Optional[str] = None):
        """
        Take user query + feedback and call LLM upto max_function_calls=10
        Handle function execution as well via helper function
        return : Json
        """
        system_prompt = prompts.create_system_prompt_mindmap_query()
        user_query, user_id, session_id, chat_id = user_request.user_query, user_request.user_id, user_request.session_id, user_request.chat_id
        
        cache_chat_logs = chat_logs_cache.get((user_id, session_id, chat_id))
        if cache_chat_logs:
            logger.info(f"Hit Cache: {cache_chat_logs}")
        else: 
            logger.info(f"Miss cache: {user_id, session_id, chat_id}")

        messages =  cache_chat_logs if cache_chat_logs else [{"role": "system", "content": system_prompt}]

        if error_feedback:
            messages.append({'role':'user',
                             "content": f"Previous response had errors: {error_feedback}. Please fix and provide a corrected response for: {user_query}"})
        else:
            messages.append({'role':'user', 'content':user_query})

        function_calls_made = []
        for _ in range(self.llm_config.max_function_calls): # Prevent infinite loops
            response_obj = await self._call_llm(messages, True)
            response_message = response_obj.choices[0].message
            if hasattr(response_message, 'function_call') and response_message.function_call:
                function_response, function_calls_executed = self._handle_function_call(response_message)
                messages.extend(function_response)
                function_calls_made.extend(function_calls_executed)
            else:
                final_content = response_message.content
                messages = messages + [{"role":"assistant", "content":response_message.content}]
                break
            
        # If we exit the loop without breaking, then following else executes in python
        else:
            # If we hit max_function_calls, get a final response anyway
            response_obj =  await self._call_llm(
                messages=messages + [{"role": "user", "content": "Please provide your final response based on the function calls you've made."}],
                tool_usage=False
            )
            messages = messages + [{"role": "user", "content": "Please provide your final response based on the function calls you've made."}],
            final_content = response_obj.choices[0].message.content
            messages = messages + [{"role":"assistant", "content":final_content}]

        try:
            response_json = json.loads(final_content)
            # Add function calls to response if they exist
            output = OutputResponse(
                main_response = response_json,
                function_calls = function_calls_made if function_calls_made else [],
                full_response = response_obj,
                chat_log = messages
            )
            return output
        except Exception as e:
            logger.warning(f"Initial LLM response is not Json Will try to parse Json. Error: {e}")
        try:
            validated_json = extract_first_json_chunk(final_content)
            output = OutputResponse(
                main_response=validated_json,
                function_calls = function_calls_made if function_calls_made else [],
                full_response = response_obj,
                chat_log = messages
            )
            return output
        except Exception as e:
            logger.error(f"Bad final content could not parse jsons. Error {e}")
