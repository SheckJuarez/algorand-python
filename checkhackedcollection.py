#!/usr/bin/python3.9
import requests
from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction
import json
import sys
import time

MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"
found = False

_maladdress = "MVEKYHFLJ63UKDYGNKCJD7WO5KFJZFVFMJPSDAWLDIDP4LUP575YDOW6GI"
senders = []

collections = ['KVC4EZQTW7M3RQWJZZXVDJ7W6THDKK7SEOKAYYSXVBN3U6HD3KKNZ2QL4E','SNUAAVKRAB7S3LRZDDJOOW77U6UVZU333BCBKWF6F6SQAF5IPVWEJKCXHI','R4V3NQKUDJKQWV74JZWEVDNJ6HMHHZK253FGMRQHAE6RA5MAKXBCYVVLQE']
allholders = []

def getnfd(addr):
	data = None
	nfd = addr
	url = "https://api.nf.domains/nfd/v2/address?address=" + addr
	resp = requests.get(url=url)
	if resp.status_code == 200:
		data = resp.json()
		nfd = data[addr][0]["name"]

	return nfd


def get_holders(indexer_client, creator):
	asalist = []
	addresses = []
	address_list = []

	next_token = None

	while True:
		try:

			payload = indexer_client.lookup_account_asset_by_creator(creator, next_page=next_token)
			for i in payload["assets"]:
				asalist.append(i["index"])

			next_token = payload.get('next-token', None)
			if next_token is None:
				break

		except Exception as e:
			print (e)


	for asset_id in asalist:
		next_token = None
		asset_holders = []
		while True:
			try:
				payload = indexer_client.asset_balances(asset_id, next_page=next_token)
				for addr in payload["balances"]:
					if addr["amount"] > 0:
						if not addr["address"] in addresses:
							addresses.append(addr["address"])
							print (addr)

				next_token = payload.get('next-token', None)
				if next_token is None:
					break
			except Exception as e:
				print(e)

	return addresses


def get_transactions(indexer_client, address):
	try:
		global found
		next_token = None
		payload = indexer_client.search_transactions_by_address(address, next_page=next_token)

		for transaction in payload["transactions"]:
			if not transaction['sender'] in senders:
				senders.append(transaction['sender'])
				if transaction['sender'] in allholders:
					print ("Holder Hit: " + getnfd(transaction['sender']))



			next_token = payload.get('next-token', None)
			if next_token is None:
				break

	except Exception as e:
		print(e)


def load_holders(indexer_client):
	global allholders
	for coll in collections:
		holders = get_holders(indexer_client, coll)
		for holder in holders:
			if not holder in allholders:
				allholders.append(holder)



def doit():
	global found
	idx_client = indexer.IndexerClient(indexer_token="", indexer_address=MAINNET_INDEXER_API)
	load_holders(idx_client)
	while 1==1: #loop forever
		get_transactions(idx_client, _maladdress)
		time.sleep(30)



doit()
 
