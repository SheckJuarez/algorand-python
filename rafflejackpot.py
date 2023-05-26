#!/usr/bin/python3.9


from algosdk.v2client import indexer, algod
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn, wait_for_confirmation
from algosdk import account, mnemonic
from algosdk import transaction

import sys, os
import requests
import json
import sys
import time
import base64
import datetime
from dateutil import parser
import pytz
import random

utc=pytz.UTC

def getalgodnet():
	try:
		with open("/var/lib/algorand/algod.net", 'r') as file:
			algod_url = "http://" + file.read().strip()
			return algod_url
	except FileNotFoundError:
		print(f"File '{file_path}' not found.")
		return None


algod_address = getalgodnet()
algod_token = "algod.token"
algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address)
mnemonic_secret = "" #Sender WOOTXGEMSBI5X5C5CR6QBS4CH2ULCKR5Y3AVNY7C6X2YZZE7O4AKLSAPRM


dest_acct = "The account address to send assets to"
MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"
found = False

naniteid = 891443534
raffleaddresses = ["XBKKRZEKKCRAOZWAU34X6FTKEYNXK46NXETOWF6ZPGXB7QHLBRNMWD5BXY", "L4XNMTND6W3U7UI57K4K3H7OA62527M6L2A5Y5K34WLHADVPXSFPLAGUOE"]
raffleids = {}
entrants = []

started = False
#firstblock = 23642751
firstblock = 28000000
startblock = sys.maxsize
endblock = sys.maxsize


def getnfd(addr):
	data = None
	nfd = addr
	url = "https://api.nf.domains/nfd/v2/address?address=" + addr
	resp = requests.get(url=url)
	if resp.status_code == 200:
		data = resp.json()
		nfd = data[addr][0]["name"]

	return nfd


def sendnanite(algod_client, winner, amt):
	global mnemonic_secret
	global naniteid

	resp = None

	try:


		sk = mnemonic.to_private_key(mnemonic_secret)
		pk = account.address_from_private_key(sk)

		params = algod_client.suggested_params()
		params.fee = 1000
		params.flat_fee = True

		account_info = algod_client.account_info(pk)
		txn = AssetTransferTxn(
				sender=pk,
				sp=params,
				receiver=winner,
				amt=amt,
				note="Project R4V3N Raffle Jackpot " + str(datetime.datetime.now())[0:19],
				index=naniteid)
		stxn = txn.sign(sk)
		txid = algod_client.send_transaction(stxn)
		wait_for_confirmation(algod_client, txid)

		resp = txid

	except Exception as e:
		print (e)


	return resp


def pickwinner(indexer_client, entries):
	winner = None
	winner = entries[random.randint(0, len(entries)-1)]
	if optedintonanite(indexer_client, winner): ###and not getnfd(winner) == winner:
		return winner
	else:
		print (winner + " not opted into NANITE. Picking new winner...")
		entries.remove(winner)
		winner = pickwinner(indexer_client, entries)

	return winner


def validateentrytx(rTicketAsId, rTicketCost, rTicketsMax, tAssetID, tAmt):

	resp = rTicketAsId == tAssetID
	resp = resp and  tAmt <= rTicketsMax * rTicketCost
	resp = resp and tAmt % rTicketCost == 0

	return resp


def cleanentrants(raffleids, entrants):
	entries = []
	for entrant in entrants:
		if entrant["rId"] in raffleids:
			if validateentrytx(raffleids[entrant["rId"]]["rTicketAsId"], raffleids[entrant["rId"]]["rTicketCost"], raffleids[entrant["rId"]]["rTicketsMax"], entrant["asset-id"], entrant["amt"]) and entrant["entrant"] not in entries:
				entries.append(entrant["entrant"])
	return entries

def optedintonanite(indexer_client, address):
	resp = False


	payload = indexer_client.lookup_account_assets(address=address, asset_id=naniteid)
	for asset in payload["assets"]:
		if asset["asset-id"] == naniteid:
			resp = True
			break

	return resp

def get_transactions(indexer_client, address):
	try:
		global raffleids
		global entrants
		global started
		global found
		global allholders
		global firstblock
		global startblock
		global endblock
		next_token = None
		note = ""

		while startblock > firstblock:
			if started == False:
				payload = indexer_client.search_transactions_by_address(address, next_page=next_token)
				started = True
			else:
				payload = indexer_client.search_transactions_by_address(address, min_round=startblock, max_round=endblock, next_page=next_token)

			i = 0
			for transaction in payload["transactions"]:
				if i == 0:
					endblock = transaction["confirmed-round"]
				else:
					startblock = transaction["confirmed-round"]


				if "note" in transaction:
					try:
						note = ""
						note = json.loads(base64.b64decode(transaction["note"]).decode('utf-8'))
					except ValueError as e:
						pass

				if "rId" in note:
					if "rCreator" in note:
						if note["rId"] not in raffleids and parser.parse(note["rEnd"]) >= utc.localize(datetime.datetime.now()):
							raffleids[note["rId"]] = note
					else:
						if "asset-transfer-transaction" in transaction:
							if transaction["asset-transfer-transaction"]["amount"] > 0:
								entrants.append({'entrant': transaction["sender"], 'rId': note["rId"], 'amt': transaction["asset-transfer-transaction"]["amount"], 'asset-id': transaction["asset-transfer-transaction"]["asset-id"]})


				i = i + 1
				next_token = payload.get('next-token', None)
				if next_token is None:
					break

			endblock = startblock
			startblock = startblock - 100000

	except Exception as e:
		print(e)
		print (sys.exc_info())



def doit():
	global started
	global firstblock
	global startblock
	global endblock
	global found
	global allholders
	global raffleids
	global algod_client

	idx_client = indexer.IndexerClient(indexer_token="", indexer_address=MAINNET_INDEXER_API)
	for raffleaddress in raffleaddresses:
		started = False
		firstblock = 23642751
		startblock = sys.maxsize
		endblock = sys.maxsize
		get_transactions(idx_client, raffleaddress)

	print ("##############################################################")
	entries = cleanentrants(raffleids, entrants)
	winner = pickwinner(idx_client, entries)
	txid = sendnanite(algod_client, winner, random.randint(100, 300))
	print ("Transaction: " + str(txid))


doit()
