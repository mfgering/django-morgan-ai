from django.contrib import admin
from .models import Assistant, Chat, Thread, ChatFavorite, ChatFlag
import decimal

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
# Register your models here.

admin.site.register(Assistant, AssistantAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(ChatFavorite, ChatFavoriteAdmin)
admin.site.register(ChatFlag, ChatFlagAdmin)