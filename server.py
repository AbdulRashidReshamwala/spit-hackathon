import json
import os
import config
from math import radians, sin, cos, acos
import random
import string
import qrutils
from cryptography.fernet import Fernet
from ip2geotools.databases.noncommercial import DbIpCity
import base64
from flask import Flask, render_template,jsonify,redirect,session,request,flash,url_for
from web3 import Web3
from dbutility import create_connection
import pickle
from passlib.hash import sha256_crypt
from datetime import datetime,timezone

web3 = Web3(Web3.HTTPProvider(config.endpoint))

app = Flask(__name__)
app.secret_key = 'its_super_secret'
UPLOADS_FOLDER = 'static/uploads'
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER

with open('abi.json') as f:
    abi = json.load(f)

with open('.key','rb') as f:
    key = f.read()
cipher = Fernet(key)

contract = web3.eth.contract(address=config.contract_address,abi= abi)
chain_id = web3.eth.chainId

def gen_key():
    key = ''.join(random.choices(string.ascii_uppercase +string.ascii_lowercase+
                             string.digits, k = 16)) 
    return key


@app.route('/')
def index():
    su = contract.functions.superuser().call()
    return render_template('login.html')

@app.route('/login',methods = ['POST'])
def login():
    # print(request.form)
    c, _ = create_connection()
    c.execute('SELECT * FROM user WHERE email=? ',
              (request.form['email'],))
    data = c.fetchone()
    if data and sha256_crypt.verify(request.form['password'], data[3]):
        session['logged_in'] = True
        session['data'] = data
        add = pickle.loads(session['data'][2])['address']
        session['address'] = Web3.toChecksumAddress(add)
        if data[4] == 1:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('node_dashboard'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('index'))
    return redirect('dashboard')


@app.route('/admin/create-node',methods = ['GET','POST'])
def create_node():
    if request.method == 'GET':
        if session['data'][4] == 1:
            print(session['data'][4])
            return render_template('create-node.html')
        else:
            return 'nononon'
    node_data = request.form
    # print(node_data['password'])
    account = session['data'][2]
    su_account = pickle.loads(account)
    su_account = web3.eth.account.privateKeyToAccount(web3.eth.account.decrypt(su_account,'Admin@123'))
    # print(su_account)
    nonce = web3.eth.getTransactionCount(su_account.address)
    node_acc = web3.eth.account.create()
    # print(node_acc.address)
    encryted_node = web3.eth.account.encrypt(node_acc.privateKey,node_data['password'])
    node_pickle = pickle.dumps(encryted_node)
    password = sha256_crypt.hash(node_data['password'])
    c, conn= create_connection()
    c.execute(
        'INSERT INTO user (email,data,password,type) VALUES( ?, ?, ?,?)', (node_data['email'],node_pickle,password,node_data['level']))
    conn.commit()
    trxn = contract.functions.addNode(node_data['name'],int(node_data['level']),node_data['lat'],node_data['lon'],node_acc.address).buildTransaction({
        'chainId':chain_id,
        'gas': 700000,
        'gasPrice': web3.toWei('1', 'gwei'),
        'nonce': nonce,
    })
    singed_trn = web3.eth.account.sign_transaction(trxn,private_key=su_account.privateKey)
    web3.eth.sendRawTransaction(singed_trn.rawTransaction)
    return 'hello'

@app.route('/admin/create-batch',methods= ['POST','GET'])
def create_batch():
    if request.method == 'GET':
        if session['data'][4] == 1:
            print(session['data'][4])
            return render_template('create-batch.html')
        else:
            return 'nonono'
    else:
        batch_data = request.form
        account = session['data'][2]
        su_account = pickle.loads(account)
        su_account = web3.eth.account.privateKeyToAccount(web3.eth.account.decrypt(su_account,'Admin@123'))
        nonce = web3.eth.getTransactionCount(su_account.address)
        timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        secret = gen_key()
        print(secret)
        id = contract.functions.batchCount().call()
        qr_data = {}
        qr_data['id'] = id 
        qr_data['hash']=sha256_crypt.encrypt(secret)
        print(qr_data)
        qrutils.generate_qr(qr_data)
        d = qrutils.decoder(f'static/qr/batch-{id}.png')
        print('result'+str(sha256_crypt.verify(secret,d['hash'])))
        secret = base64.b64encode(cipher.encrypt(secret.encode()))
        trxn = contract.functions.addBatch(batch_data['origin'],batch_data['name'],str(timestamp),secret).buildTransaction({
            'chainId':chain_id,
            'gas': 700000,
            'gasPrice': web3.toWei('1', 'gwei'),
            'nonce': nonce,
        })
        singed_trn = web3.eth.account.sign_transaction(trxn,private_key=su_account.privateKey)
        web3.eth.sendRawTransaction(singed_trn.rawTransaction)
        return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    print(request.remote_addr)
    batch_count = contract.functions.batchCount().call()
    batch = []
    for i in range(batch_count):
        batch.append(contract.functions.batchMapping(i).call())
    print(batch)
    node_count = contract.functions.nodeCount().call()
    nodes = []
    for i in range(node_count):
        nodes.append(contract.functions.nodeMapping(contract.functions.nodeIds(i).call()).call())
    print(nodes)
    return render_template('admin-dashboard.html',nodes = nodes)

@app.route('/node')
def node_dashboard():
    add = session['address']
    print(add)
    node_details = contract.functions.nodeMapping(add).call()
    node_batch_ids = contract.functions.nodeBatches(add).call()
    batchs = []
    for id in node_batch_ids:
        batchs.append(contract.functions.batchMapping(id).call())
    print(node_details)
    return render_template('batch.html',batchs = batchs)

@app.route('/node/<add>')
def node_view(add):
    node_details = contract.functions.nodeMapping(add).call()
    node_batch_ids = contract.functions.nodeBatches(add).call()
    batchs = []
    for id in node_batch_ids:
        batchs.append(contract.functions.batchMapping(id).call())
    print(batchs)
    return render_template('batch.html',batchs = batchs)

@app.route('/batch/<id>')
def get_batch(id):
    id = int(id)
    batch = contract.functions.batchMapping(id).call()
    stops_ids = contract.functions.viewStops(id).call()
    stops = []
    nodes = []
    for stops_id in stops_ids:
        stop = contract.functions.stopMapping(stops_id).call()
        stops.append(stop)
        nodes.append(contract.functions.nodeMapping(stop[0]).call())
    # status = cipher.decrypt(base64.b64decode(batch[2])).decode()
    print(len(stops))
    print(nodes)
    img = f'qr/batch-{batch[0]}.png'
    return render_template('map-trace.html',batch = batch,nodes = nodes,stops = stops,count = len(stops),img=img)

@app.route('/node/accept-batch', methods = ['GET','POST'])
def add_stop():
    if request.method == 'POST':
        ip = request.remote_addr
        # r = request.environ.get('HTTP_X_REAL_IP', ip)
        response = DbIpCity.get('125.99.120.242',api_key='free')
        node = contract.functions.nodeMapping(session['address']).call()
        dist = (6371.01 * acos(sin(float(node[5]))*sin(response.latitude) + cos(float(node[5]))*cos(response.latitude)*cos(float(node[6]) - response.longitude))) * 1000
        print('ans:='+str(dist))
        f = request.files['file']
        f.filename = 'temp.png'
        apath = os.path.join(app.config['UPLOADS_FOLDER'], f.filename)
        f.save(apath)
        data= qrutils.decoder(apath)
        id = data['id']
        sec = contract.functions.batchMapping(id).call()[2]
        sec = cipher.decrypt(base64.b64decode(sec)).decode()
        print(sha256_crypt.verify(sec,data['hash']))
        id= int(id)
        timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        timestamp = str(timestamp)
        account = session['data'][2]
        account = pickle.loads(account)
        account = web3.eth.account.privateKeyToAccount(web3.eth.account.decrypt(account,'Node@123'))
        nonce = web3.eth.getTransactionCount(account.address)
        trxn = contract.functions.acceptBatch(id,timestamp).buildTransaction({
                'chainId':chain_id,
                'gas': 700000,
                'gasPrice': web3.toWei('1', 'gwei'),
                'nonce': nonce,
            })
        singed_trn = web3.eth.account.sign_transaction(trxn,private_key=account.privateKey)
        web3.eth.sendRawTransaction(singed_trn.rawTransaction)
        return redirect('/batch/'+str(id))
    else:
        return render_template('scan.html')

@app.route('/verification',methods = ['GET','POST'])
def verification():
    if request.method == 'POST':
        f = request.files['file']
        f.filename = 'temp.png'
        apath = os.path.join(app.config['UPLOADS_FOLDER'], f.filename)
        f.save(apath)
        data= qrutils.decoder(apath)
        id = data['id']
        sec = contract.functions.batchMapping(id).call()[2]
        sec = cipher.decrypt(base64.b64decode(sec)).decode()
        status = sha256_crypt.verify(sec,data['hash'])
        batch = contract.functions.batchMapping(id).call()
        stops_ids = contract.functions.viewStops(id).call()
        stops = []
        nodes = []
        for stops_id in stops_ids:
            stop = contract.functions.stopMapping(stops_id).call()
            stops.append(stop)
            nodes.append(contract.functions.nodeMapping(stop[0]).call())
        return render_template('batch-ver.html',status=status,nodes=nodes,stops = stops,batch = batch )
    else:
        return render_template('verify.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug= True)
