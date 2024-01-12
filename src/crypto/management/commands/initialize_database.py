import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from time import sleep
from typing import Dict, List

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import F
from django.db.utils import IntegrityError
from tronpy import Tron
from tronpy.keys import PrivateKey, PublicKey
from tronpy.exceptions import AddressNotFound
from requests.exceptions import HTTPError
import time
from pathlib import Path
import re

from crypto.models import (
    Address,
    ChainTron,
    ChainAdminAddress,
    ChainAddress,
    ChainTronName
)

def match_name_id(name: str):
    match name:
        case "mainnet":
            return (ChainTronName.MAINNET, 0)
        case "shasta":
            return (ChainTronName.SHASTA, 1)
        case "tronex":
            return (ChainTronName.TRONEX, 2)
        case "nile":
            return (ChainTronName.NILE, 3)
        case _:
            raise Exception("Wrong network name")

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--network', 
            choices=['mainnet', 'testnet'], 
            default="mainnet",
            help='Specify the network (mainnet or testnet)'
        )
    def handle(self, *args, **options):
        network = options['network']
        dir = Path(__file__).resolve().parent.parent.parent.parent
        config = dir / "config.txt"
        with open(config, "r") as f:
            try:
                l = f.readlines()
                i = 0
                
                while True:
                    line = re.sub("^\s+|\n|\r|\s+$", '', l[i])
                    match line:
                        case "#Chains":
                            while True:
                                i += 1
                                line = re.sub("^\s+|\n|\r|\s+$", '', l[i])
                                if line != "end":
                                    name, minimum_balance, refill_value = line.split(":")
                                    minimum_balance = int(minimum_balance) * 10 ** 6
                                    refill_value = int(refill_value) * 10 ** 6
                                    name, id = match_name_id(name)
                                    chain, b = ChainTron.objects.get_or_create(
                                        id=id, 
                                        name=name, 
                                        symbol="TRX",
                                        minimum_balance=minimum_balance,
                                        refill_value=refill_value
                                    )
                                    if b:
                                        logging.info(f"Create chain {chain.name}")
                                    else:
                                        logging.info(f"Chain {chain.name} already exists!")
                                    continue
                                break
                        case "#Admins":
                            while True:
                                i += 1
                                line = re.sub("^\s+|\n|\r|\s+$", '', l[i])
                                if line != "end":
                                    addr, pk = line.split(":")
                                    name, _ = match_name_id(network)
                                    chain = ChainTron.objects.get(name=name)
                                    with transaction.atomic():
                                        try:
                                            address, _ = Address.objects.get_or_create(address=addr)
                                            ChainAdminAddress.objects.create(
                                                address=address, 
                                                private_key=pk, 
                                                chain=chain
                                            )
                                            logging.info(f"Create chain admin address {address.address} (chain: {chain.name})")
                                        except IntegrityError:
                                            logging.info(f"Chain Admin address {address.address} already exists!")
                                        except Exception as e:
                                            logging.info(f"Accured an exception: {e}")
                                    continue
                                break
                        case "#Address":
                            while True:
                                i += 1
                                line = re.sub("^\s+|\n|\r|\s+$", '', l[i])
                                if line != "end":
                                    name, _ = match_name_id(network)
                                    chain = ChainTron.objects.get(name=name)
                                    with transaction.atomic():
                                        try:
                                            address, _= Address.objects.get_or_create(address=line)
                                            ChainAddress.objects.create(
                                                address=address, 
                                                chain=chain
                                            )
                                            logging.info(f"Create chain address {address.address} (chain: {chain.name})")
                                        except IntegrityError:
                                            logging.info(f"Chain address {address.address} already exists!")
                                        except Exception as e:
                                            logging.info(f"Accured an exception: {e}")
                                    continue
                                break
                        case _:
                            raise Exception("The config.txt is wrong!")
                    i += 1
            except IndexError:
                logging.info(f"Database initialized!")
            except Exception as e:
                logging.info(f"Accured an exception: {e}")
