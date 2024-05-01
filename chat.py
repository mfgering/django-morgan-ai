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
            break #TODO: REMOVE THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        
    async def say(self, msg: str):
        if not self.messages:
            self._init_system_messages()
            tools = self._init_tools()
        self.messages.append(self._user(msg).to_json())
        while True:
            response = await self.client.chat.completions.create(model=self.model_name, messages=self.messages, tools=tools)
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                m = response.choices[0].message
                if not m.content:
                    m.content = ''
                self.messages.append(response.choices[0].message)  # extend conversation with assistant's reply
                # Send the info for each function call and function response to the model
                for tool_call in tool_calls:
                    fn_resp_msg = morgan.functions.call_tool(tool_call)
                    self.messages.append(fn_resp_msg)
                response = await self.client.chat.completions.create(
                    model=self.model_name, messages=self.messages)  # get a new response from the model where it can see the function response

            self._last_response = response
            self._last_message = response.choices[0].message
            content = self._last_message.content
            m = Message(self._last_message.role, content, 'assistant')
            print(f"{content} ({self._last_response.usage.total_tokens} total tokens)")
            if self._last_response.choices[0].finish_reason == 'stop':
                break
    
    def _user(self, msg: str):
        m = Message('user', msg, 'user')
        return m
    
chat = MorganChat()

asyncio.run(chat.say('How large is unit 412 and is unit number 600 valid?'))

