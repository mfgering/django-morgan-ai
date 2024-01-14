from django.contrib import admin
from .models import Chat, Thread, ChatFavorite
import decimal

class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at', 'status')

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at')

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'openai_id', 'created_at')

class ChatFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'flagged', 'rank', 'user_msg', 'assist_msg')
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


# Register your models here.

admin.site.register(Chat, ChatAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(ChatFavorite, ChatFavoriteAdmin)