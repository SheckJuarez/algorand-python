#!/usr/bin/python3.9
import requests
from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction
import json
import sys

MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"
found = False

_address = "XEVZQJCGTMPA62BZ6KDOVHWDM3LDB4KLD7WGBYH3E6XHCRLPBZQV2MBF6Y"

def get_transactions(indexer_client, address):
	try:
		print(f"Starting...")
		next_token = None
		payload = indexer_client.search_transactions_by_address(address, next_page=next_token)

		for transaction in payload["transactions"]:
			if "rekey-to" in transaction:
				if transaction["rekey-to"]:
					found = True
					print(json.dumps(transaction, indent=4))
					print ("########################################################################")
					print ("########################################################################")
					print ("########################################################################")

			next_token = payload.get('next-token', None)
			if next_token is None:
				break

	except Exception as e:
		print(e)



def doit():
	idx_client = indexer.IndexerClient(indexer_token="", indexer_address=MAINNET_INDEXER_API)
	get_transactions(idx_client, _address)
	if not found:
		print ("Account not rekeyed")

doit()

