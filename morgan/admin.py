from django.contrib import admin
from .models import Chat, Message, Thread, ChatFavorite

class MessageInline(admin.TabularInline):
    model = Message

class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at', 'thread', 'status')

class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ('id', 'openai_id', 'created_at')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'content', 'created_at', 'thread_ref')
    def content(self, obj):
        result = obj.content if len(obj.content) < 30 else obj.content[:30]+'...'
        return result

class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ('id', 'openai_id', 'created_at')

class ChatFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'flagged', 'rank', 'user_msg', 'assist_msg')

# Register your models here.

admin.site.register(Chat, ChatAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatFavorite, ChatFavoriteAdmin)