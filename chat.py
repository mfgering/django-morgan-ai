import openai
import os
import json
import morgan_proj.settings
from dataclasses import dataclass
import asyncio
from datetime import datetime
import morgan.functions

@dataclass
class Message(json.JSONEncoder):
    role: str
    content: str
    name: str

    def to_json(self):
        return self.__dict__

class MorganChat:
    def __init__(self, api_key=None) -> None:
        self.model_name = "gpt-4-turbo-preview"
        self.client = openai.AsyncClient(api_key=morgan_proj.settings.OPENAI_API_KEY)
        self.messages = []
        self._system_prompt = None

    def _init_tools(self):
        tools = morgan.functions.all_tool_defs
        return tools
    
    def _init_system_messages(self):
        self.messages = []
        file_map = [
            ['prompt', f"Today is {datetime.now().strftime('%A, %B %d, %Y')}.\n", 'morgan/static/files/prompt-no-files.txt'],
            ['faqs', 'Frequently asked questions:', 'morgan/static/files/dawson_faqs.txt'],
            ['covenants', 'The Dawson Covenants Condominium covenants are rules that maintain '
                        'order and protect property values in a condo community by setting '
                        'standards for behavior, property alterations, and use of common areas, '
                        'ensuring a harmonious living environment for all residents.'
                        'Identify the Article, Section, and Clause for for references to Covenants.', 'morgan/static/files/dawson_covenants-2005-split.txt'],

            ['bylaws', 'The Dawson Bylaws define the '
                        'operation and management of the community. They outline responsibilities '
                        'of the HOA and owners, regulate the use of spaces, establish governance, '
                        'manage finances, provide dispute resolution methods, and protect property '
                        'values. for questions about the Bylaws and identify the Article and '
                        'Section where possible.'
                        'Identify the Article, Section, and Clause for for references to Bylaws.', 'morgan/static/files/dawson_bylaws-split.txt'], 
            ['rules', 'These are the Rules and Regulations in markdown format. Rules and Regulations '
                        'define how responsibilities are shared between the HOA and the HOMEOWNER. '
                        'Each rule has a number. For example, rule number 30 begins '
                        '"**30. WINDOW/DOOR SCREENS**" Include the rule number when referring this '
                        'content.', 'morgan/static/files/dawson_rules.txt'],
            ['maintenance', 'Maintenance Responsibilities:', 'morgan/static/files/dawson_rules.txt'],
        ]
        for name, intro, fn in file_map:
            with open(fn, 'r') as f:
                txt = f.read()
            m = Message('system', f'{intro}\n{txt}', name)
            self.messages.append(m.to_json())

        
    async def say(self, msg: str):
        if not self.messages:
            self._init_system_messages()
        #m = self._user(msg)
        self.messages.append(self._user(msg).to_json())
        tools = self._init_tools()
        response = await self.client.chat.completions.create(model=self.model_name, messages=self.messages, tools=tools)
        tool_calls = response.tool_calls
        if tool_calls:
            pass
            available_functions = {
                "get_unit_info": morgan.functions.get_unit_info,
            }  # only one function in this example, but you can have multiple
            self.messages.append(response.choices[0].message)  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    prop=function_args.get("prop"),
                    unit=function_args.get("unit"),
                )
                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
            response = await self._client.chat.completions.create(
                model=self.model_name, messages=self.messages)  # get a new response from the model where it can see the function response

        self._last_response = response
        self._last_message = response.choices[0].message
        content = self._last_message.content
        m = Message(self._last_message.role, content, 'assistant')
        print(f"{content} ({self._last_response.usage.total_tokens} total tokens)")
    
    def _user(self, msg: str):
        m = Message('user', msg, 'user')
        return m
    
chat = MorganChat()

asyncio.run(chat.say('What rules are there about cats?'))

