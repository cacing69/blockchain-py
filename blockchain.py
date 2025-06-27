import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests

from urllib.parse import urlparse

class Blockchain(object):
    difiiculty_target =  "0000" # The difficulty target for proof of work

    def hash_block(self, block):
        block_encode = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encode).hexdigest()

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        genesis_hash = self.hash_block("genesis_block")

        self.append_block(
            hash_of_previous_block = genesis_hash,
            nonce = self.proof_of_work(0, genesis_hash, []),
        )

    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0

        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()

        content_hash = hashlib.sha256(content).hexdigest()

        return content_hash[:len(self.difiiculty_target)] == self.difiiculty_target

    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'hash_of_previous_block': hash_of_previous_block,
            'nonce': nonce
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def add_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()

#routes
@app.route("/blockchain", methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }

    return jsonify(response), 200

@app.route("/mine", methods=['GET'])
def mine_block():
    blockchain.add_transaction(
        sender="0",  # This signifies that the node has mined a new block
        recipient=node_identifier,
        amount=1,  # Reward for mining a block
    )

    last_block_hash = blockchain.hash_block(blockchain.last_block)

    index = len(blockchain.chain)

    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)

    block = blockchain.append_block(nonce, last_block_hash)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
    }

    return jsonify(response), 200

@app.route("/transaction/new", methods=['POST'])
def new_transaction():
    values = request.get_json()

    required_fields = ['sender', 'recipient', 'amount']
    if not all(field in values for field in required_fields):
        return jsonify({
            'errors': 'Missing values'
        }), 400

    index = blockchain.add_transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount'],
    )

    response = {
        'message': f'Transaction will be added to Block {index}'
    }

    return jsonify(response), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))  # Default port is 5000, can be overridden by command line argument
    # To run the server, use: python blockchain.py <port_number>
    # Example: python blockchain.py 5000
    # This will start the Flask server on the specified port.
    # Make sure to install Flask and requests libraries if not already installed.
    # You can install them using pip:
    # pip install Flask requests
    # Ensure you have Python 3.x installed to run this code.