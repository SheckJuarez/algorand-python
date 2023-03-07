#!/usr/bin/python3.9
#from algosdk import algod
from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction
import os
import json
import ipfshttpclient


#api = ipfsapi.connect('127.0.0.1', 5001)
MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"
asalist = []

def get_holders(indexer_client, asalist):


	next_token = None

	try:
		payload = indexer_client.account_info(address="Add Your Address Here")
		for asset in payload["account"]["assets"]:
			print (asset)
			assetid = int(asset["asset-id"])
			asalist.append(assetid)
			print (assetid)

	except Exception as e:
		print (e)




def doit():

	idx_client = indexer.IndexerClient(indexer_token="", indexer_address=MAINNET_INDEXER_API)
	get_holders(idx_client, asalist)

	print (asalist)

doit()

