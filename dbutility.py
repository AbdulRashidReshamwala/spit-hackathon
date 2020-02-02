import pickle 
import sqlite3
import config
import json
from web3 import Web3
from passlib.hash import sha256_crypt

web3 = Web3(Web3.HTTPProvider(config.endpoint))

admin_publickey = '0xDa477e55Db92b4B94BD45e20026c59461c79aDE8'
admin_privatekey = '433f1e6d8b1e8df41a3020d692f01c62f20032723c982d8f5363869163b356e7'
admin_password = 'Admin@123'

nodes_pk = ['1db118c51397bed99195c8fa7b9231c8de8733f5133d5ddbdd9b72452d41df8d','ec3fee50ea6dd1407bcb9ed830314d1192ee0910c65e40c4f75cabca8674ad82','c281f7c89551b8b715e103854fc0fa99292a8bd91f825471bd1410136b4bbf4f','7fe50e6776b58358a7d4559bd4f194677d409e38d7c44a1d85ef4d788175db3f','e43b2b4186dff410dc7e5b83e4bb4af907dcc09a8d3f47d8b4e25ae232402623']

nodes_name = ['Processing Plant 1','Research Center 1','Processing Plant 2','Research Center 2','Store 1']

node_level = [2,3,2,3,4]

node_lat_lon = [('19.1238','72.8361'),('37.4275','122.1697'),('32.4275','127.1697'),('42.3770','71.1167'),('45.3601','73.0942')]

node_password = 'Node@123'

with open('abi.json') as f:
    abi = json.load(f)

contract = web3.eth.contract(address=config.contract_address,abi= abi)

chain_id = web3.eth.chainId


def create_connection():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    return c, conn

def create_table():
    c, _ = create_connection()
    user_query = '''CREATE TABLE user(
        id integer PRIMARY KEY AUTOINCREMENT,
        email text UNIQUE NOT NULL,
        data blob NOT NULL,
        password text NOT NULL,
        type integer NOT NULL
    )'''
    c.execute(user_query)


def create_admin():
    admin_password = 'Admin@123'
    account = web3.eth.account.encrypt(admin_privatekey,admin_password)
    data = pickle.dumps(account)
    admin_password = sha256_crypt.hash(admin_password)
    c, conn= create_connection()
    c.execute(
        'INSERT INTO user (email,data,password,type) VALUES( ?, ?, ?,?)', ('admin@admin.com',data,admin_password,1))
    conn.commit()


def create_nodes():
    for i, key in enumerate(nodes_pk):
        enc_acc = web3.eth.account.encrypt(key,node_password)
        enc_acc_dump = pickle.dumps(enc_acc)
        password = sha256_crypt.hash(node_password)
        c, conn= create_connection()
        c.execute(
            'INSERT INTO user (email,data,password,type) VALUES( ?, ?, ?, ?)', (f'node{i}@node.com',enc_acc_dump,password,node_level[i]))
        conn.commit()
        add = Web3.toChecksumAddress(enc_acc['address'])
        nonce = web3.eth.getTransactionCount(admin_publickey)
        trxn = contract.functions.addNode(nodes_name[i],node_level[i],node_lat_lon[i][0],node_lat_lon[i][1],add).buildTransaction({
            'chainId':chain_id,
            'gas': 700000,
            'gasPrice': web3.toWei('1', 'gwei'),
            'nonce': nonce,
        })
        singed_trn = web3.eth.account.sign_transaction(trxn,private_key=admin_privatekey)
        web3.eth.sendRawTransaction(singed_trn.rawTransaction)
        print(contract.functions.nodeCount().call())

if __name__ == "__main__":
    create_table()
    create_admin()
    create_nodes()