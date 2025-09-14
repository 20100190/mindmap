from pydantic import BaseModel
import openai
import os
from . import tools
import json
from . import prompts
from typing import Optional, Any

class LLMConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    temperature: float = 0.3
    timeout: int = 100  # seconds
    max_function_calls: int=10

def get_llm_config() -> LLMConfig:
    return LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        max_retries=os.getenv("OPENAI_MAX_RETRIES", 3),
        temperature=os.getenv("OPENAI_TEMPERATURE", 0.3),
        timeout=os.getenv("OPENAI_TIMEOUT", 100)
        )


class LLMClient:
    def __init__(self):
        self.llm_config = get_llm_config()
        self.client = openai.AsyncOpenAI(
            api_key=self.llm_config.api_key,
            base_url=self.llm_config.base_url,
            timeout=self.llm_config.timeout
    )
        
    async def process_query(self, user_query, error_feedback: Optional[str] = None):
        system_prompt = prompts.create_system_prompt_mindmap_query()

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if error_feedback:
            messages.append({'role':'user',
                             "content": f"Previous response had errors: {error_feedback}. Please fix and provide a corrected response for: {user_query}"})
        else:
            messages.append({'role':'user', 'content':user_query})

        function_calls_made = []
        max_function_calls = self.llm_config.max_function_calls  # Prevent infinite loops    
        for call_iteration in range(max_function_calls):
            response = await self.client.chat.completions.create(
                        model=self.llm_config.model,
                        temperature=self.llm_config.temperature,
                        messages=messages,
                        functions=tools.define_functions(),
                        function_call="auto"
                    )   
            
            message = response.choices[0].message
            
            # Check if LLM wants to call a function
            if hasattr(message, 'function_call') and message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                
                # Execute the function
                function_result = tools.execute_function_call(function_name, function_args)
                
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
                    "content": function_result
                })
                
                # Continue the loop to see if LLM wants to call another function
                
            else:
                final_content = message.content
                break
        # If we exit the loop without breaking, then following else executes in python
        else:
            # If we hit max_function_calls, get a final response anyway
            final_response =  await self.client.chat.completions.create(
                model=self.llm_config.model,
                messages=messages + [{"role": "user", "content": "Please provide your final response based on the function calls you've made."}]
            )

            final_content = final_response.choices[0].message.content

        try:
            response_json = json.loads(final_content)
            # Add function calls to response if they exist
            if function_calls_made:
                response_json["function_calls"] = function_calls_made
            return response_json
        except json.JSONDecodeError:
            # If not JSON, wrap in expected format
            return {
                "status": "success",
                "data": {"response": final_content},
                "function_calls": function_calls_made,
                "message": "Response generated successfully"
            }
