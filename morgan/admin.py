from django.contrib import admin
from django.contrib import messages
from .models import Assistant, Chat, Thread, ChatFavorite, ChatFlag
import decimal
import requests
from django.conf import settings
import json
from datetime import datetime
import openai

class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at', 'status')
    actions = ["collect_garbage"]
    @admin.action(description="Collect garbage")

    def collect_garbage(self, request, queryset):
        for chat in queryset:
            if len(chat.msgs) < 5:
                chat.delete()

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at')

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at')

class ChatFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'flagged', 'faq', 'fav', 'rank', 'user_msg', 'assist_msg')
    actions = ["normalize_rank"]

    @admin.action(description="Normalize the rank values")
    def normalize_rank(self, request, queryset):
        favs = queryset.order_by("rank")
        num_favs = favs.count()
        if num_favs > 0:
            incr = decimal.Decimal(100 / num_favs)
            rank_num = decimal.Decimal(favs[0].rank)
            for fav in favs:
                fav.rank = rank_num
                rank_num += incr
                fav.save()
        return num_favs

class ChatFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'user_txt', 'asst_txt', 'flag_txt')

class AssistantAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'openai_id')
    actions = ["assistant_update_openai"]

    def assistant_update_openai(self, request, queryset):
        client = openai.OpenAI()
        for assistant in queryset:
            try:
                openai_assistant = openai.beta.assistants.retrieve(assistant.openai_id)
                assistant.name = openai_assistant.name
                assistant.description = openai_assistant.description
                assistant.created_at = datetime.utcfromtimestamp(openai_assistant.created_at)
                assistant.model = openai_assistant.model
                assistant.instructions = openai_assistant.instructions
                assistant.save()
            except Exception as exc:
                messages.add_message(request=request, level=messages.ERROR, 
                                     message=f"Error with assistant {assistant.name}: {exc}")

# Register your models here.

admin.site.register(Assistant, AssistantAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(ChatFavorite, ChatFavoriteAdmin)
admin.site.register(ChatFlag, ChatFlagAdmin)