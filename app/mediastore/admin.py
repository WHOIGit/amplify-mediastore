from django.contrib import admin

from .models import StoreConfig, S3Config, IdentifierType

class StoreConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'type', 'bucket', 's3cfg__url', 's3cfg__pk')
    def s3cfg__url(self, obj):
        return obj.s3cfg.url if obj.s3cfg else ''
    def s3cfg__pk(self, obj):
        return obj.s3cfg.pk if obj.s3cfg else ''

class S3ConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'url', 'access_key')

class IdentityTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(StoreConfig,StoreConfigAdmin)
admin.site.register(S3Config,S3ConfigAdmin)
admin.site.register(IdentifierType, IdentityTypeAdmin)
