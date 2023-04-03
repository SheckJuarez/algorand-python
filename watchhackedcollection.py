#!/usr/bin/python3.9
import requests
from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk import transaction
import json
import sys
import time

MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"
found = False

_maladdress = "MVEKYHFLJ63UKDYGNKCJD7WO5KFJZFVFMJPSDAWLDIDP4LUP575YDOW6GI"
senders = []

collections = ['KVC4EZQTW7M3RQWJZZXVDJ7W6THDKK7SEOKAYYSXVBN3U6HD3KKNZ2QL4E', 'SNUAAVKRAB7S3LRZDDJOOW77U6UVZU333BCBKWF6F6SQAF5IPVWEJKCXHI',
               'R4V3NQKUDJKQWV74JZWEVDNJ6HMHHZK253FGMRQHAE6RA5MAKXBCYVVLQE', 'R4V3NBVSRDR5UF3JNODCKBHO5IC6RG74SEJEOA3SVMB2XNQB6YBXGC3WF4']
allholders = []

block_height = 0


def getnfd(addr):
    data = None
    nfd = addr
    url = "https://api.nf.domains/nfd/v2/address?address=" + addr
    resp = requests.get(url=url)
    if resp.status_code == 200:
        data = resp.json()
        nfd = addr + " nfd:" + data[addr][0]["name"]

    return nfd


def check_rekey(indexer_client, address):
    isRekeyed = False
    next_token = None
    while True:
        try:
            payload = indexer_client.search_transactions_by_address(
                address, next_page=next_token, txn_type="pay", rekey_to=True)

            for transaction in payload["transactions"]:
                if "rekey-to" in transaction and transaction["sender"] == address:
                    isRekeyed = True
                    print("Account: " + address + " rekeyed to " +
                          transaction["rekey-to"] + " in round: " + str(transaction["confirmed-round"]))

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

        except Exception as e:
            print(e)

    return isRekeyed


def get_holders(indexer_client, creator):
    asalist = []
    addresses = []

    next_token = None

    while True:
        try:

            payload = indexer_client.lookup_account_asset_by_creator(
                creator, next_page=next_token)
            for i in payload["assets"]:
                asalist.append(i["index"])

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

        except Exception as e:
            print(e)

    for asset_id in asalist:
        next_token = None
        while True:
            try:
                payload = indexer_client.asset_balances(
                    asset_id, next_page=next_token)
                for addr in payload["balances"]:
                    if addr["amount"] > 0:
                        if not addr["address"] in addresses:
                            addresses.append(addr["address"])
                            print(addr)

                next_token = payload.get('next-token', None)
                if next_token is None:
                    break
            except Exception as e:
                print(e)

    return addresses


def get_transactions(indexer_client, address):
    global block_height
    last_round = block_height + 1
    print("Getting transactions for round >= " + str(last_round))
    next_token = None
    while True:
        try:
            global found
            payload = indexer_client.search_transactions_by_address(
                address, next_page=next_token, min_round=block_height)
            if len(payload["transactions"]):
                if payload["transactions"][0]['confirmed-round'] > last_round:
                    last_round = payload["transactions"][0]['confirmed-round']
                print("Current transactions batch round: " +
                      str(payload["transactions"][0]['confirmed-round']))
            for transaction in payload["transactions"]:
                if not transaction['sender'] in senders:
                    senders.append(transaction['sender'])
                    if transaction['sender'] in allholders:
                        print("Holder Hit: " + getnfd(transaction['sender']))

            next_token = payload.get('next-token', None)
            if next_token is None:
                break
        except Exception as e:
            print(e)

    block_height = last_round


def load_holders(indexer_client):
    global allholders
    for coll in collections:
        holders = get_holders(indexer_client, coll)
        for holder in holders:
            if not check_rekey(indexer_client, holder):
                if not holder in allholders:
                    allholders.append(holder)


def doit():
    global found
    global allholders
    idx_client = indexer.IndexerClient(
        indexer_token="", indexer_address=MAINNET_INDEXER_API)
    load_holders(idx_client)
    print(allholders)
    get_transactions(idx_client, _maladdress)
    while 1 == 1:  # loop forever
        print("Checking Transactions")
        get_transactions(idx_client, _maladdress)
        time.sleep(60)


doit()
