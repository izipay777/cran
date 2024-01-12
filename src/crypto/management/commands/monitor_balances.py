import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from time import sleep
from typing import Dict, List

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import F
from tronpy import Tron
from tronpy.keys import PrivateKey, PublicKey
from tronpy.exceptions import AddressNotFound
from requests.exceptions import HTTPError
import time

from crypto.models import (
    Address,
    ChainTron,
    ChainAdminAddress,
    ChainAddress
)

def decor(*args, function):
    while True:
        try:
            result = function(*args)
            return result
        except HTTPError:
            logging.info(f"Rate limit! sleep")
            sleep(1)

def get_admin(tron: Tron, admins: List[ChainAdminAddress]):
    for admin in admins:
        bandwidth = decor(
            "wallet/getaccountnet", 
            {
                "address": admin.address.address, 
                "visible": True
            }, 
            function=tron.provider.make_request
        )

        if not (bandwidth["freeNetLimit"] - bandwidth.get("freeNetUsed", 0) > 0):
            logging.info(f"Insuficient admin's bandwidth")
            continue

        return admin
    
    logging.warning("All administrators have run out of bandwidth")

    return admin[0]

def check_balances(address: ChainAddress, current_block:int, admins: List[ChainAdminAddress]):
    try:
        while True:

            if address.last_checked_block >= current_block:
               break
            latest_block = current_block

            # if current_block - address.last_checked_block > 100:
            #    latest_block = address.last_checked_block + 100
            # else:
            #    latest_block = current_block

            tron: Tron = address.chain.web3
            chain: ChainTron = address.chain
            minimum_balance = chain.minimum_balance
            refill_value = int(chain.refill_value)

            logging.info(
                    f"  Last remembered block: {address.last_checked_block}, current last: {latest_block}"
                )
            logging.info(
                    f"  Checking blocks {address.last_checked_block} ~ {latest_block} ({address.address.address})"
                )

            with transaction.atomic():
                try:
                    # update balances
                    try:
                        address.address.balance = decor(
                            address.address.address, 
                            function=tron.get_account_balance
                        ) * 10 ** 6
                    except AddressNotFound:
                        logging.info(
                            f"Need to initialize address {address.address.address} or address balance is zero"
                        )
                    # chain.admin_balance = tron.get_account_balance(chain.admin_public) * 10 ** 6
                    logging.info(
                        f"Check address {address.address.address} balance for minimum balance\n\
                        Adress balance is {int(address.address.balance / 10 ** 6)} TRX"
                    )

                    # check balance
                    if address.address.balance < minimum_balance:
                        
                        admin = get_admin(tron, admins)
                        try:
                            admin.address.balance = decor(
                                admin.address.address, 
                                function=tron.get_account_balance
                            ) * 10 ** 6
                        except AddressNotFound:
                            logging.warning(
                                f"Need to initialize ADMIN address {address.address.address} \
                                    or ADMIN address balance is zero"
                            )

                        # send transaction for refill value(40 TRX) from admin address
                        if admin.address.balance < refill_value:
                            logging.error(f"Insufficient admin's balance")
                        else:
                            pk = admin.get_private_key_instance()
                            tx = (
                                tron.trx.transfer(admin.address.address, address.address.address, refill_value)
                                .build()
                                .sign(pk)
                            )
                            while True:
                                try:
                                    tx.broadcast().wait()
                                    break
                                except HTTPError:
                                    logging.info(f"Rate limit! sleep")
                                    sleep(1)
                            logging.info(f"Sent {refill_value} TRX to {address.address.address} (txid: {tx.txid}")

                        admin.address.save(update_fields=("balance",))

                    address.last_checked_block = latest_block
                    address.save(update_fields=("last_checked_block",))
                    address.address.save(update_fields=("balance",))

                except Exception as e:
                    logging.error(f"Accured an exception: {e}")
                    

    except KeyboardInterrupt:
        return
    except HTTPError:
        logging.info(f"Rate limit! sleep")
        sleep(1)
    except:
        traceback.print_exc()


class Command(BaseCommand):
    def handle(self, *args, **options):
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures: Dict[int, Future] = {}
            while True:
                for k, fut in list(futures.items()):
                    if fut.done():
                        del futures[k]
                try:
                    for chain in ChainTron.objects.all():
                        try:
                            """
                            You can use sleep mode to reduce the number of API requests.

                            The TRON network produces a block around every 3s, 
                            and thus it usually doesn’t make sense 
                            to request new data at a faster speed.
                            """
                            sleep(10)
                            

                            tron: Tron = chain.web3
                            current_block = decor(function=tron.get_latest_block_number)
                            admins = ChainAdminAddress.objects.filter(chain=chain)
                            need_update = ChainAddress.objects.filter(
                                chain=chain, last_checked_block__lt=current_block
                            )
                            
                            if need_update.count():
                                for address in need_update:
                                    if address.pk not in futures:
                                        futures[address.pk] = executor.submit(
                                            check_balances,
                                            address,
                                            current_block,
                                            admins
                                        )
                        except:
                            print(traceback.format_exc())
                except KeyboardInterrupt:
                    return
                except:
                    traceback.print_exc()

                try:
                    sleep(0)
                except KeyboardInterrupt:
                    return
