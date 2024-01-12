from django.db import models
from django.utils.translation import gettext
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from tronpy import Tron 
from tronpy.providers import HTTPProvider as tron_provider
from django.conf import settings
from django.core import exceptions

from tronpy.keys import is_base58check_address, PrivateKey

class ChainTronName(models.TextChoices):
    SHASTA = "shasta"
    MAINNET = "mainnet"
    NILE = "nile"
    TRONEX ="tronex"

class TronAddressField(models.CharField):
    """
    A custom Django model for storing Tron addresses.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the TronAddressField.
        """
        kwargs.setdefault("max_length", 34)
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        if value:
            try: 
                is_base58check_address(value)
            except:
                raise exceptions.ValidationError('Invalid Tron address')
        return value
    

    
class ChainTron(models.Model):
    id = models.IntegerField(primary_key=True)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=32, unique=True, choices=ChainTronName.choices)

    minimum_balance = models.DecimalField(default=3e+7, decimal_places=0, max_digits=50)
    refill_value = models.DecimalField(default=4e+7, decimal_places=0, max_digits=50)

    class Meta:
        verbose_name = "Chain"
        verbose_name_plural = "Chains"

    @property
    def web3(self):
        if self.name == "mainnet":
            tron = Tron(tron_provider(api_key=settings.TRON_API_KEY, timeout=60))
            return tron
        tron = Tron(network=self.name)
        return tron

    def __str__(self):
        return f"{self.name} (ChainTron ID: {self.id})"
    
class Address(models.Model):
    address = TronAddressField(unique=True)
    balance = models.DecimalField(decimal_places=0, default=0, max_digits=64)

    class Meta:
        verbose_name = "Adress"
        verbose_name_plural = "Adresses"
    
    def __str__(self):
        return self.address
    

class ChainAddress(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="chain_addresses")
    chain = models.ForeignKey(ChainTron, on_delete=models.CASCADE, related_name="addresses")
    last_checked_block = models.PositiveBigIntegerField(default=0)
    
    class Meta:
        unique_together = (
            "address",
            "chain",
        )
        verbose_name = "Chain Adress"
        verbose_name_plural = "Chain Adresses"
    @staticmethod
    def get(address: str, chain: ChainTron):
        address, _ =  Address.objects.get_or_create(
            address=address, chain=chain
        )
        return address


class ChainAdminAddress(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="chain_admin_addresses")
    chain = models.ForeignKey(ChainTron, on_delete=models.CASCADE, related_name="admin_addresses")
    private_key = models.CharField(max_length=64)
    class Meta:
        unique_together = (
            "address",
            "chain",
        )
        verbose_name = "Chain Admin Adress"
        verbose_name_plural = "Chain Admin Adresses"
    
    def get_private_key_instance(self) -> PrivateKey:
        return PrivateKey(bytes.fromhex(self.private_key))
    