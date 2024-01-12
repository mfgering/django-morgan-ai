from django.db import models
from django.utils import timezone
from django.conf import settings
import json
import requests

def get_openai_headers():
    headers = {
      "Content-Type": "application/json",
      'OpenAI-Beta': "assistants=v1",
      'Authorization': f"Bearer {settings.OPENAI_API_KEY}"
    }
    return headers

# Create your models here.

class Assistant(models.Model):
    ASSISTANT_ID = 'asst_G0tCzhuvOi8cqtUnUwMCKXhx'
    openai_id = models.CharField(max_length=256, null=True)
    created_at = models.DateTimeField(null=True)
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=512, null=True)
    model = models.CharField(max_length=512, null=True)
    # Note: Other OpenAI fields are not modeled here

    def _str_(self):
        return self.name

class Thread(models.Model):
    openai_id = models.CharField(max_length=256, null=True)
    created_at = models.DateTimeField(null=True)

    def get_thread_data(self):
        endpoint = f"https://api.openai.com/v1/threads/{self.openai_id}"
        r = requests.get(endpoint, headers=get_openai_headers())
        openai_data = json.loads(r.text)
        return openai_data

    def get_messages(self):
        endpoint = f"https://api.openai.com/v1/threads/{self.openai_id}/messages"
        r = requests.get(endpoint, headers=get_openai_headers())
        openai_data = json.loads(r.text)
        return openai_data

class Run(models.Model):
    openai_id = models.CharField(max_length=256, null=True)
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(null=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=256, null=True)

class Chat(Run):
    DEFAULT_CHARACTER_NAME = 'Morgan'

    DEFAULT_GREETING = f"Hi. I'm **{DEFAULT_CHARACTER_NAME}**, your AI assistant for The Dawson. " \
        "I can help you with things related to The Dawson on Morgan, " \
        "like answering questions and providing information about the property and its operation. " \
        "Though my answers my be useful, they are **not** authoritative. " \
        "How can I help you?"
    ASSISTANT_ROLE = 'assistant'
    USER_ROLE = 'user'
    character_name = models.CharField(max_length=256, default=DEFAULT_CHARACTER_NAME)
    greeting = models.TextField(default=DEFAULT_GREETING)
    msgs = models.CharField(max_length=30000, default=DEFAULT_CHARACTER_NAME)

class ChatFavorite(models.Model):
    rank = models.DecimalField(max_digits=5, decimal_places=2, default=-1)
    flagged = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    user_msg = models.TextField(null=True)
    assist_msg = models.TextField(null=True)
