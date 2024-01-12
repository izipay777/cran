from django.contrib import admin

from .models import ChainTron, Address, ChainAdminAddress, ChainAddress

@admin.register(ChainTron)
class ChainTronAdmin(admin.ModelAdmin):
    list_display = ["symbol", "name", "minimum_balance", "refill_value"]

@admin.register(Address)
class ChainAddressAdmin(admin.ModelAdmin):
    list_display = ["address", "balance"]

@admin.register(ChainAddress)
class ChainAddressAdmin(admin.ModelAdmin):
    list_display = ["address", "last_checked_block", "chain"]
    list_filter = ["chain"]

@admin.register(ChainAdminAddress)
class ChainAdminAddressAdmin(admin.ModelAdmin):
    list_display = ["address", "chain", "private_key"]
    list_filter = ["chain"]