from django.contrib import admin
from .models import Assistant, Chat, Thread, ChatFavorite, ChatFlag
import decimal
import requests
from django.conf import settings
import json
from datetime import datetime

def get_openai_headers():
    headers = {
      "Content-Type": "application/json",
      'OpenAI-Beta': "assistants=v1",
      'Authorization': f"Bearer {settings.OPENAI_API_KEY}"
    }
    return headers

class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at', 'status')

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
        for assistant in queryset:
            endpoint =f"https://api.openai.com/v1/assistants/{assistant.openai_id}"
            r = requests.get(endpoint, headers=get_openai_headers())
            if r.status_code == 200:
                openai_data = json.loads(r.text)
                assistant.name = openai_data['name']
                assistant.created_at = datetime.utcfromtimestamp(openai_data['created_at'])
                assistant.model = openai_data['model']
                assistant.instructions = openai_data['instructions']
                assistant.save()

# Register your models here.

admin.site.register(Assistant, AssistantAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(ChatFavorite, ChatFavoriteAdmin)
admin.site.register(ChatFlag, ChatFlagAdmin)