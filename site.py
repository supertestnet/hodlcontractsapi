import os
import math
import time
import json
import requests
import random
import hashlib
import sqlite3
import base64
import codecs
import binascii
from hashlib import sha256 as hexsha
from flask import Flask, redirect, url_for, request, make_response, render_template, send_file, send_from_directory
from flask_cors import CORS
from os.path import exists

with open( "mailgun-key.txt" ) as file:
    lines = file.read()
    mailgunkey = lines.split( '\n', 1 )[ 0 ]

file_exists = exists( "password.txt" )
if file_exists:
    with open( "password.txt" ) as file:
        lines = file.read()
        adminpassword = lines.split( '\n', 1 )[ 0 ]
else:
    password = "password"
    with open( "password.txt", "w" ) as file:
        file.write( password )

salt = password
def sha256( string ):
    hash = hashlib.sha256( string.encode( 'utf-8' ) ).hexdigest()
    return hash

def hexhash( hex ):
    str = hex
    begin = 0
    end = 2
    halfstrlength = len( str ) / 2
    newstr = ""
    for x in range( halfstrlength ):
        newstr = newstr + "\\x" + str[begin:end]
        begin = begin + 2
        end = end + 2
    newstr = newstr + ""
    rawhex4 = newstr.decode( 'string-escape' )
    h1 = hexsha()
    h1.update(rawhex4)
    return h1.hexdigest()

def makeRandomString():
    rand1 = random.randrange( 10000000, 99999999 )
    rand2 = random.randrange( 10000000, 99999999 )
    rand3 = random.randrange( 10000000, 99999999 )
    rand4 = random.randrange( 10000000, 99999999 )
    rand5 = random.randrange( 10000000, 99999999 )
    rand6 = random.randrange( 10000000, 99999999 )
    rand7 = random.randrange( 10000000, 99999999 )
    rand8 = random.randrange( 10000000, 99999999 )
    allrand = str( rand1 ) + str( rand2 ) + str( rand3 ) + str( rand4 ) + str( rand5 ) + str( rand6 ) + str( rand7 ) + str( rand8 )
    return sha256( allrand )

def lookupuser( session_id ):
    currenttime = int( math.floor( time.time() ) )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user, expiry from sessions WHERE session_id = '" + session_id + "'" )
    session = cur.fetchone()
    sjson = json.dumps( session )
    con.close()
    if ( session[ 1 ] < currenttime ):
        return
    user = session[ 0 ]
    return user

def lookupemail( user ):
    user = str( user )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT email from users WHERE user_id = '" + user + "'" )
    session = cur.fetchone()
    sjson = json.dumps( session )
    con.close()
    email = session[ 0 ]
    return email

def loginuser( user ):
    session_id = makeRandomString()
    currenttime = int( math.floor( time.time() ) )
    session_expiry = currenttime + 604800
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO sessions VALUES( :user, :session_id, :expiry )", { "user": str( user ), "session_id": str( session_id ), "expiry": str( session_expiry ) } )
    con.commit()
    con.close()
    status = {
        "status": "success",
        "id": str( user ),
        "session": str( session_id ),
        "expiry": str( session_expiry )
    }
    sjson = json.dumps( status )
    return sjson

def isThereABuyer( tx_id ):
    tx_id = str( tx_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    buyer = tdata[ "buyer" ]
    if ( not tdata[ "buyer" ] or tdata[ "buyer" ] == "" ):
        return 0
    else:
        return 1

def setbuyer( user, tx_id ):
    tx_id = str( tx_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": str( user ),
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": tdata[ "status" ],
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data, buyer = :buyer WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id, "buyer": str( user ) } )
    con.commit()

def sendemail( to, subject, body, attachment ):
    email_text = body

    email_subject = subject
    with open( "./templates/email-template.html" ) as f:
        html = f.read()
    html = html.format( email_subject=email_subject, email_text=email_text )
    import requests

    key = mailgunkey
    sandbox = 'mg.lightningescrow.io'
    recipient = to

    request_url = 'https://api.mailgun.net/v3/{0}/messages'.format(sandbox)
    if ( attachment == "None" ):
        request = requests.post(request_url, auth=('api', key), data={
            'from': 'no-reply@lightningescrow.io',
            'to': recipient,
            'subject': subject,
            'html': html
        })
    else:
        file_url = attachment
        attachment = open( file_url, 'rb' )
        request = requests.post(request_url, auth=('api', key), data={
            'from': 'no-reply@lightningescrow.io',
            'to': recipient,
            'subject': subject,
            'html': html,
            'attachment': attachment
        })

    print 'Status: {0}'.format(request.status_code)
    print 'Body:   {0}'.format(request.text)

def checkpmthash( invoice, desiredhash ):
    url = 'https://localhost:8080/v1/payreq/' + invoice
    cert_path = '/root/.lnd/tls.cert'
    macaroon = codecs.encode(open('/root/.lnd/data/chain/bitcoin/mainnet/admin.macaroon', 'rb').read(), 'hex')
    headers = {'Grpc-Metadata-macaroon': macaroon}
    r = requests.get(url, headers=headers, verify=cert_path)
    pmtdata = r.json()
    invhash = pmtdata[ "payment_hash" ]
    if ( invhash == desiredhash ):
        return 1
    else:
        return 0

def initdbs():
    file_exists = exists( "lnescrow.db" )
    if not file_exists:
        with open( "lnescrow.db","w" ) as file:
            file.write( "" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( """CREATE TABLE IF NOT EXISTS users (
        user text,
        user_id text,
        email text
        )""" )
    con.commit()
    con.close()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( """CREATE TABLE IF NOT EXISTS transactions (
        transaction_data text,
        transaction_id text,
        seller text,
        buyer text
        )""" )
    con.commit()
    con.close()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( """CREATE TABLE IF NOT EXISTS preimages (
        transaction_id text,
        preimage text
        )""" )
    con.commit()
    con.close()
#tx data: creation, expiry, shippping link, contract id
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( """CREATE TABLE IF NOT EXISTS sessions (
        user text,
        session_id text,
        expiry text
        )""" )
    con.commit()
    con.close()

initdbs()

app = Flask( __name__, static_url_path="", static_folder="static" )
CORS( app )

@app.route( '/setuser/', methods=[ 'POST', 'GET' ] )
def setuser():
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user from users" )
    users = cur.fetchall()
    con.close()
    count = len( users )
    id = count
    if request.form.get( "fname" ):
        fname = request.form.get( "fname" )
    else:
        fname = ""
    if request.form.get( "fname" ):
        lname = request.form.get( "lname" )
    else:
        lname = ""
    email = request.form.get( "email" )
    password = sha256( str( request.form.get( "password" ) ) + salt )
    joined = str( int( math.floor( time.time() ) ) )
    user = {
        "id": id,
        "fname": fname,
        "lname": lname,
        "email": email,
        "password": password,
        "joined": joined
    }
    ujson = json.dumps( user )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO users VALUES( :user, :user_id, :email )", { "user": ujson, "user_id": str( user[ "id" ] ), "email": str( user[ "email" ] ) } )
    con.commit()
    con.close()
    sjson = loginuser( str( user[ "id" ] ) )
    if ( request.form.get( "tx" ) ):
        tx_id = request.form.get( "tx" )
        if ( isThereABuyer( tx_id ) == 0 ):
            setbuyer( int( user[ "id" ] ), int( request.form.get( "tx" ) ) )
    return sjson

@app.route( '/setuser/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/setuser/v2/', methods=[ 'POST', 'GET' ] )
def setuserv2():
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user from users" )
    users = cur.fetchall()
    con.close()
    count = len( users )
    id = count
    fname = ""
    lname = ""
    email = request.json[ "email" ]
    password = sha256( str( request.json[ "password" ] ) + salt )
    joined = str( int( math.floor( time.time() ) ) )
    user = {
        "id": id,
        "fname": fname,
        "lname": lname,
        "email": email,
        "password": password,
        "joined": joined
    }
    ujson = json.dumps( user )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO users VALUES( :user, :user_id, :email )", { "user": ujson, "user_id": str( user[ "id" ] ), "email": str( user[ "email" ] ) } )
    con.commit()
    con.close()
    sjson = loginuser( str( user[ "id" ] ) )
    if ( "tx" in request.json ):
        tx_id = request.json[ "tx" ]
        if ( isThereABuyer( tx_id ) == 0 ):
            setbuyer( int( user[ "id" ] ), int( request.json[ "tx" ] ) )
    return sjson

@app.route( '/getuser/', methods=[ 'POST', 'GET' ] )
def getuser():
    user_id = request.args.get( "user" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user from users WHERE user_id = '" + user_id + "'" )
    user = cur.fetchone()
    user = user[ 0 ]
    con.close()
    return user

@app.route( '/settx/', methods=[ 'POST', 'GET' ] )
def settx():
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions" )
    transactions = cur.fetchall()
    con.close()
    count = len( transactions )
    id = count
    if request.form.get( "goods_or_services" ):
        goods_or_services = request.form.get( "goods_or_services" )
    else:
        goods_or_services = "n/a"
    if request.form.get( "title" ):
        title = request.form.get( "title" )
    else:
        title = "n/a"
    if request.form.get( "description" ):
        description = request.form.get( "description" )
    else:
        description = "n/a"
    if request.form.get( "fee_payer" ):
        fee_payer = request.form.get( "fee_payer" )
    else:
        fee_payer = "n/a"
    if request.form.get( "amount" ):
        amount = request.form.get( "amount" )
    else:
        amount = "n/a"
    if request.form.get( "buyer_email" ):
        buyer_email = request.form.get( "buyer_email" )
    else:
        buyer_email = "n/a"
    created = int( math.floor( time.time() ) )
    expires = created + 604800
    status = "needs invoice"
    preimage = makeRandomString()
    transaction = {
        "id": id,
        "shipping_link": "",
        "created": created,
        "expires": expires,
        "buyer": "",
        "buyer_email": buyer_email,
        "seller": user,
        "goods_or_services": goods_or_services,
        "title": title,
        "description": description,
        "fee_payer": fee_payer,
        "amount": amount,
        "status": status,
        "pmthash": hexhash( preimage ),
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO transactions VALUES( :transaction_data, :transaction_id, :seller, :buyer )", { "transaction_data": tjson, "transaction_id": str( transaction[ "id" ] ), "seller": str( user ), "buyer": "" } )
    con.commit()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO preimages VALUES( :transaction_id, :preimage )", { "transaction_id": str( transaction[ "id" ] ), "preimage": str( preimage ) } )
    con.commit()
    status = {
        "status": "success",
        "id": str( transaction[ "id" ] )
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( user )
    body = """
        <p>Hello,</p>
	<br>
        <p>{seller_email} has invited you to start a transaction using LightningEscrow. Please sign up or login using this email to complete the next steps to start the transaction process.</p>
	<br>
        <p style="text-decoration: underline;">Transaction details</p>
	<br>
        <p>Title: {txtitle}</p>
	<br>
        <p>Details: {txdetails}</p>
	<br>
        <p>BTC Requested amount: {txamount}</p>
	<br>
        <p>Date created: {txcreated}</p>
	<br>
        <p>Expiration date: {txexpires}</p>
	<br>
        <p>Transaction ID: {txid}</p>
	<br>
        <p>If you have any questions, check out our FAQ page for more details.</p>
	<br>
        <p><a href="https://lightningescrow.io/">LightningEscrow.io</a></p>
	<br>
        <a href="https://app.lightningescrow.io/{txlink}"><button style="padding: 10px; background-color: lightgreen; color: white; font-weight: bold; border-radius: 10px; cursor: pointer;">Start Transaction</button></a>
    """.format( seller_email=seller_email, txtitle=title, txdetails=description, txamount=amount + " sats", txcreated=time.ctime( created ), txexpires=time.ctime( expires ), txid=str( transaction[ "id" ] ), txlink="buyer-payment.html?tx=" + str( transaction[ "id" ] ) + "&email=" + buyer_email )
    sendemail( buyer_email, 'Invitation to start transaction', body, "None" )
    return sjson

@app.route( '/settx/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/settx/v2/', methods=[ 'POST', 'GET' ] )
def settxv2():
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions" )
    transactions = cur.fetchall()
    con.close()
    count = len( transactions )
    id = count
    if ( "goods_or_services" in request.json ):
        goods_or_services = request.json[ "goods_or_services" ]
    else:
        goods_or_services = "n/a"
    if ( "title" in request.json ):
        title = request.json[ "title" ]
    else:
        title = "n/a"
    if ( "description" in request.json ):
        description = request.json[ "description" ]
    else:
        description = "n/a"
    if ( "fee_payer" in request.json ):
        fee_payer = request.json[ "fee_payer" ]
    else:
        fee_payer = "n/a"
    if ( "amount" in request.json ):
        amount = str( request.json[ "amount" ] )
    else:
        amount = "n/a"
    if ( "buyer_email" in request.json ):
        buyer_email = request.json[ "buyer_email" ]
    else:
        buyer_email = "n/a"
    created = int( math.floor( time.time() ) )
    expires = created + 604800
    status = "needs invoice"
    preimage = makeRandomString()
    transaction = {
        "id": id,
        "shipping_link": "",
        "created": created,
        "expires": expires,
        "buyer": "",
        "buyer_email": buyer_email,
        "seller": user,
        "goods_or_services": goods_or_services,
        "title": title,
        "description": description,
        "fee_payer": fee_payer,
        "amount": amount,
        "status": status,
        "pmthash": hexhash( preimage ),
    }
    tjson = json.dumps( transaction )
    tnum = str( transaction[ "id" ] )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO transactions VALUES( :transaction_data, :transaction_id, :seller, :buyer )", { "transaction_data": tjson, "transaction_id": str( transaction[ "id" ] ), "seller": str( user ), "buyer": "" } )
    con.commit()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "INSERT INTO preimages VALUES( :transaction_id, :preimage )", { "transaction_id": str( transaction[ "id" ] ), "preimage": str( preimage ) } )
    con.commit()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + str( transaction[ "id" ] ) + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    status = {
        "status": "success",
        "data": {
            "id": tnum,
            "shipping_link": "",
            "created": created,
            "expires": expires,
            "buyer": "",
            "buyer_email": buyer_email,
            "seller": user,
            "goods_or_services": goods_or_services,
            "title": title,
            "description": description,
            "fee_payer": fee_payer,
            "amount": amount,
            "status": status,
            "pmthash": hexhash( preimage ),
        }
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( user )
    body = """
        <p>Hello,</p>
	<br>
        <p>{seller_email} has invited you to start a transaction using LightningEscrow. Please sign up or login using this email to complete the next steps to start the transaction process.</p>
	<br>
        <p style="text-decoration: underline;">Transaction details</p>
	<br>
        <p>Title: {txtitle}</p>
	<br>
        <p>Details: {txdetails}</p>
	<br>
        <p>BTC Requested amount: {txamount}</p>
	<br>
        <p>Date created: {txcreated}</p>
	<br>
        <p>Expiration date: {txexpires}</p>
	<br>
        <p>Transaction ID: {txid}</p>
	<br>
        <p>If you have any questions, check out our FAQ page for more details.</p>
	<br>
        <p><a href="https://lightningescrow.io/">LightningEscrow.io</a></p>
	<br>
        <a href="https://app.lightningescrow.io/{txlink}"><button style="padding: 10px; background-color: lightgreen; color: white; font-weight: bold; border-radius: 10px; cursor: pointer;">Start Transaction</button></a>
    """.format( seller_email=seller_email, txtitle=title, txdetails=description, txamount=amount + " sats", txcreated=time.ctime( created ), txexpires=time.ctime( expires ), txid=tnum, txlink="buyer-payment.html?tx=" + tnum + "&email=" + buyer_email )
    sendemail( buyer_email, 'Invitation to start transaction', body, "None" )
    return sjson

@app.route( '/setinvoice', methods=[ 'POST', 'GET' ] )
@app.route( '/setinvoice/', methods=[ 'POST', 'GET' ] )
def setinvoice():
    tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    invoice = request.form.get( "invoice" )
    desiredhash = tdata[ "pmthash" ]
    if ( not checkpmthash( invoice, desiredhash ) ):
        return ""
    seller = tdata[ "seller" ]
    if ( "invoice" in tdata and tdata[ "invoice" ] != "" ):
        return ""
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    status = "needs paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": invoice,
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "id": str( transaction[ "id" ] )
    }
    sjson = json.dumps( status )
    return sjson

@app.route( '/setinvoice/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/setinvoice/v2/', methods=[ 'POST', 'GET' ] )
def setinvoicev2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    invoice = request.json[ "invoice" ]
    desiredhash = tdata[ "pmthash" ]
    if ( not checkpmthash( invoice, desiredhash ) ):
        return '{"status":"error", "message":"wrong payment hash, try again"}'
    seller = tdata[ "seller" ]
    if ( "invoice" in tdata and tdata[ "invoice" ] != "" ):
        return ""
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    status = "needs paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": invoice,
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "invoice": str( transaction[ "invoice" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    return sjson

@app.route( '/confirmpayment', methods=[ 'POST', 'GET' ] )
@app.route( '/confirmpayment/', methods=[ 'POST', 'GET' ] )
def confirmpayment():
    tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    if ( tdata[ "status" ] == "paid" or tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "id": str( transaction[ "id" ] )
    }
    sjson = json.dumps( status )
    return sjson

@app.route( '/confirmpayment/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/confirmpayment/v2/', methods=[ 'POST', 'GET' ] )
def confirmpaymentv2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    if ( tdata[ "status" ] == "paid" or tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    return sjson

@app.route( '/goodssent', methods=[ 'POST', 'GET' ] )
@app.route( '/goodssent/', methods=[ 'POST', 'GET' ] )
def goodssent():
    tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    if ( tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "goods sent"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "id": str( transaction[ "id" ] )
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( user )
    buyer_email = tdata[ "buyer_email" ]
    body = """
	<p>Hello {buyer_email},</p>
	<br>
	<p>Good news!</p>
	<br>
	<p>{seller_email} has shipped the goods! Please contact the seller for details on tracking. Please click the Confirm button <a href="https://app.lightningescrow.io/details-page.html?tx={txid}">on this page</a> when you receive your goods or services so that we can release the escrowed funds to the seller.</p>
	<br>
	<p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
	<br>
	<p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( buyer_email=buyer_email,seller_email=seller_email, txid=str( transaction[ "id" ] ) )
    sendemail( buyer_email, 'Goods shipped out', body, "None" )
    return sjson

@app.route( '/goodssent/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/goodssent/v2/', methods=[ 'POST', 'GET' ] )
def goodssentv2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( seller ) ):
        return ""
    if ( tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "goods sent"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( user )
    buyer_email = tdata[ "buyer_email" ]
    body = """
	<p>Hello {buyer_email},</p>
	<br>
	<p>Good news!</p>
	<br>
	<p>{seller_email} has shipped the goods! Please contact the seller for details on tracking. Please click the Confirm button <a href="https://app.lightningescrow.io/details-page.html?tx={txid}">on this page</a> when you receive your goods or services so that we can release the escrowed funds to the seller.</p>
	<br>
	<p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
	<br>
	<p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( buyer_email=buyer_email,seller_email=seller_email, txid=str( transaction[ "id" ] ) )
    sendemail( buyer_email, 'Goods shipped out', body, "None" )
    return sjson

@app.route( '/goodsreceived/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/goodsreceived/v2/', methods=[ 'POST', 'GET' ] )
def goodsreceivedv2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( buyer ) ):
        return ""
    if ( tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "goods received"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( tdata[ "seller" ] )
    buyer_email = tdata[ "buyer_email" ]
    body = """
        <p>Hello {seller_email},</p>
        <br>
        <p>Good news!</p>
        <br>
        <p>{buyer_email} says they received their goods and authorized LightningEscrow to release the payment to you. <a href="https://app.lightningescrow.io/seller-lastpage.html?tx={txid}">Click here</a> and follow the instructions to receive your BTC.</p>
        <br>
        <p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
        <br>
        <p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txid=str( transaction[ "id" ] ) )
    sendemail( seller_email, 'Buyer confirms they received the goods', body, "None" )
    body = """
        <p>Hello {buyer_email},</p>
        <br>
        <p>Thank you for using LightningEscrow. Below is a receipt attached from your recent transaction titled {txtitle}.</p>
        <br>
        <p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
        <br>
        <p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txtitle=tdata[ "title" ], txamount=tdata[ "amount" ] + " sats", txid=str( transaction[ "id" ] ) )
    sendemail( buyer_email, 'Your LightningEscrow Receipt', body, "sample.pdf" )
    return sjson

@app.route( '/goodsreceived', methods=[ 'POST', 'GET' ] )
@app.route( '/goodsreceived/', methods=[ 'POST', 'GET' ] )
def goodsreceived():
    tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( buyer ) ):
        return ""
    if ( tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "goods received"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( tdata[ "seller" ] )
    buyer_email = tdata[ "buyer_email" ]
    body = """
        <p>Hello {seller_email},</p>
        <br>
        <p>Good news!</p>
        <br>
        <p>{buyer_email} says they received their goods and authorized LightningEscrow to release the payment to you. <a href="https://app.lightningescrow.io/seller-lastpage.html?tx={txid}">Click here</a> and follow the instructions to receive your BTC.</p>
        <br>
        <p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
        <br>
        <p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txid=str( transaction[ "id" ] ) )
    sendemail( seller_email, 'Buyer confirms they received the goods', body, "None" )
    body = """
        <p>Hello {buyer_email},</p>
        <br>
        <p>Thank you for using LightningEscrow. Below is a receipt attached from your recent transaction titled {txtitle}.</p>
        <br>
        <p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
        <br>
        <p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txtitle=tdata[ "title" ], txamount=tdata[ "amount" ] + " sats", txid=str( transaction[ "id" ] ) )
    sendemail( buyer_email, 'Your LightningEscrow Receipt', body, "sample.pdf" )
    return sjson

@app.route( '/buyerpaid', methods=[ 'POST', 'GET' ] )
@app.route( '/buyerpaid/', methods=[ 'POST', 'GET' ] )
def buyerpaid():
    tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    invoice = request.form.get( "invoice" )
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( buyer ) ):
        return ""
    if ( tdata[ "status" ] == "claims paid" or tdata[ "status" ] == "paid" or tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "claims paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "id": str( transaction[ "id" ] )
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( tdata[ "seller" ] )
    buyer_email = tdata[ "buyer_email" ]
    body = """
	<p>Hello {seller_email},</p>
	<br>
	<p>Good news!</p>
	<br>
	<p>{buyer_email} says he put the agreed bitcoin amount of {txamount} into your escrow contract. Please check your node to see if the contract is really funded (<a href="https://app.lightningescrow.io/check-transaction-status.html?tx={txid}">instructions are available here</a>), then, if it is funded, ship out the good or service that you agreed to within 10 days to receive payment.</p>
	<br>
	<p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
	<br>
	<p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txamount=tdata[ "amount" ] + " sats", txid=str( transaction[ "id" ] ) )
    sendemail( seller_email, 'Money put into escrow', body, "None" )
    return sjson

@app.route( '/buyerpaid/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/buyerpaid/v2/', methods=[ 'POST', 'GET' ] )
def buyerpaidv2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    if not session_id:
        return ""
    user = lookupuser( session_id )
    if not user:
        return ""
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    if ( int( user ) != int( buyer ) ):
        return ""
    if ( tdata[ "status" ] == "claims paid" or tdata[ "status" ] == "paid" or tdata[ "status" ] == "goods sent" or tdata[ "status" ] == "goods received" or tdata[ "status" ] == "funds received" ):
        return ""
    status = "claims paid"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
    con.commit()
    status = {
        "status": "success",
        "data": {
            "id": str( transaction[ "id" ] ),
            "shipping_link": str( transaction[ "shipping_link" ] ),
            "created": str( transaction[ "created" ] ),
            "expires": str( transaction[ "expires" ] ),
            "buyer": str( transaction[ "buyer" ] ),
            "buyer_email": str( transaction[ "buyer_email" ] ),
            "seller": str( transaction[ "seller" ] ),
            "goods_or_services": str( transaction[ "goods_or_services" ] ),
            "title": str( transaction[ "title" ] ),
            "description": str( transaction[ "description" ] ),
            "fee_payer": str( transaction[ "fee_payer" ] ),
            "amount": str( transaction[ "amount" ] ),
            "status": str( transaction[ "status" ] ),
            "pmthash": str( transaction[ "pmthash" ] ),
        }
    }
    sjson = json.dumps( status )
    seller_email = lookupemail( tdata[ "seller" ] )
    buyer_email = tdata[ "buyer_email" ]
    body = """
	<p>Hello {seller_email},</p>
	<br>
	<p>Good news!</p>
	<br>
	<p>{buyer_email} says he put the agreed bitcoin amount of {txamount} into your escrow contract. Please check your node to see if the contract is really funded (<a href="https://app.lightningescrow.io/check-transaction-status.html?tx={txid}">instructions are available here</a>), then, if it is funded, ship out the good or service that you agreed to within 10 days to receive payment.</p>
	<br>
	<p><a href="https://app.lightningescrow.io/details-page.html?tx={txid}">Click here</a> to view your transaction details.</p>
	<br>
	<p>Questions or feedback? Visit us at <a href="https://lightningescrow.io/">LightningEscrow.io</a> and let us know</p>
    """.format( seller_email=seller_email, buyer_email=buyer_email, txamount=tdata[ "amount" ] + " sats", txid=str( transaction[ "id" ] ) )
    sendemail( seller_email, 'Money put into escrow', body, "None" )
    return sjson

@app.route( '/getallusertxs', methods=[ 'POST', 'GET' ] )
@app.route( '/getallusertxs/', methods=[ 'POST', 'GET' ] )
def getallusertxs():
    session_id = request.form.get( "session_id" )
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE seller = '" + user + "' OR buyer = '" + user + "'" )
    transactions = cur.fetchall()
    alltransactions = "["
    for transaction in transactions:
        alltransactions += transaction[ 0 ] + ","
    alltransactions = alltransactions[ 0:-1 ]
    alltransactions += "]"
    con.close()
    if alltransactions == "]":
        alltransactions = "[]"
    return alltransactions

@app.route( '/getallusertxs/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/getallusertxs/v2/', methods=[ 'POST', 'GET' ] )
def getallusertxsv2():
    session_id = request.json[ "session_id" ]
    user = lookupuser( session_id )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE seller = '" + user + "' OR buyer = '" + user + "'" )
    transactions = cur.fetchall()
    alltransactions = "["
    for transaction in transactions:
        alltransactions += transaction[ 0 ] + ","
    alltransactions = alltransactions[ 0:-1 ]
    alltransactions += "]"
    con.close()
    if alltransactions == "]":
        alltransactions = "[]"
    return alltransactions

@app.route( "/login", methods=[ 'POST', 'GET' ] )
@app.route( "/login/", methods=[ 'POST', 'GET' ] )
def attemptlogin():
    if ( request.form.get( "email" ) ):
        email = request.form.get( "email" )
    else:
        email = request.args.get( "email" )
    if ( request.form.get( "password" ) ):
        passedpw = request.form.get( "password" )
    else:
        passedpw = request.args.get( "password" )
    userpass = sha256( str( passedpw ) + salt )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT * from users WHERE email = '" + email + "'" )
    user = cur.fetchone()
    user_id = user[ 1 ]
    user = user[ 0 ]
    ujson = json.loads( user )
    realpassword = ujson[ "password" ]
    con.close()
    currenttime = int( math.floor( time.time() ) )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT session_id, expiry from sessions WHERE user = '" + user_id + "'" )
    session = cur.fetchone()
    con.close()
    if ( request.form.get( "tx" ) ):
        tx_id = str( request.form.get( "tx" ) )
        if ( isThereABuyer( tx_id ) == 0 ):
            setbuyer( int( user_id ), int( request.form.get( "tx" ) ) )
# If the user is already logged in, send back his current session id
    if ( session[ 1 ] > currenttime ):
        session_id = session[ 0 ]
        status = {
            "status": "success",
            "id": str( user_id ),
            "session": str( session_id ),
	    "expiry": str( session[ 1 ] )
        }
        sjson = json.dumps( status )
        if realpassword == userpass:
            return sjson
#If the user is not logged in, especially if they were logged in but their session id expired, log them in
    if realpassword == userpass:
        return loginuser( user_id )
    else:
        status = {
            "status": "error",
            "message": "wrong password",
        }
        returnable = json.dumps( status )
    return returnable

@app.route( "/login/v2", methods=[ 'POST', 'GET' ] )
@app.route( "/login/v2/", methods=[ 'POST', 'GET' ] )
def attemptloginv2():
    email = request.json[ "email" ]
    passedpw = request.json[ "password" ]
    userpass = sha256( str( passedpw ) + salt )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT * from users WHERE email = '" + email + "'" )
    user = cur.fetchone()
    user_id = user[ 1 ]
    user = user[ 0 ]
    ujson = json.loads( user )
    realpassword = ujson[ "password" ]
    con.close()
    currenttime = int( math.floor( time.time() ) )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT session_id, expiry from sessions WHERE user = '" + user_id + "'" )
    session = cur.fetchone()
    con.close()
    if ( "tx" in request.json ):
        tx_id = str( request.json[ "tx" ] )
        if ( isThereABuyer( tx_id ) == 0 ):
            setbuyer( int( user_id ), int( request.json[ "tx" ] ) )
        else:
            return '{"status":"error", "message":"this transaction already has a buyer"}'
# If the user is already logged in, send back his current session id
    if ( session[ 1 ] > currenttime ):
        session_id = session[ 0 ]
        status = {
            "status": "success",
            "id": str( user_id ),
            "session": str( session_id ),
	    "expiry": str( session[ 1 ] )
        }
        sjson = json.dumps( status )
        if realpassword == userpass:
            return sjson
#If the user is not logged in, especially if they were logged in but their session id expired, log them in
    if realpassword == userpass:
        return loginuser( user_id )
    else:
        status = {
            "status": "error",
            "message": "wrong password",
        }
        returnable = json.dumps( status )
    return returnable

@app.route( '/gettx', methods=[ 'POST', 'GET' ] )
@app.route( '/gettx/', methods=[ 'POST', 'GET' ] )
def gettx():
    tx_id = request.args.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.args.get( "session_id" )
    password = request.args.get( "password" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    user = lookupuser( session_id )
    if ( password == adminpassword ):
        return transaction
    if ( int( user ) != int( seller ) and int( user ) != int( buyer ) ):
        return ""
    return transaction

@app.route( '/gettx2', methods=[ 'POST', 'GET' ] )
@app.route( '/gettx2/', methods=[ 'POST', 'GET' ] )
def gettx2():
    tx_id = request.args.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    user = lookupuser( session_id )
    if ( int( user ) != int( seller ) and int( user ) != int( buyer ) ):
        return ""
    return transaction

@app.route( '/gettx/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/gettx/v2/', methods=[ 'POST', 'GET' ] )
def gettxv2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    seller = tdata[ "seller" ]
    if ( seller == "" ):
        seller = -1
    buyer = tdata[ "buyer" ]
    if ( buyer == "" ):
        buyer = -1
    user = lookupuser( session_id )
    if ( int( user ) != int( seller ) and int( user ) != int( buyer ) ):
        return ""
    return transaction

@app.route( '/getpreimage', methods=[ 'POST', 'GET' ] )
@app.route( '/getpreimage/', methods=[ 'POST', 'GET' ] )
def getpreimage():
    tx_id = request.args.get( "tx" )
    tx_id = str( tx_id )
    password = request.args.get( "password" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT preimage from preimages WHERE transaction_id = '" + tx_id + "'" )
    preimage = cur.fetchone()
    preimage = preimage[ 0 ]
    con.close()
    if password == adminpassword:
        return preimage
    else:
        return "nice try!"

@app.route( '/getpreimage2/', methods=[ 'POST', 'GET' ] )
def getpreimage2():
    if ( request.args.get( "tx" ) ):
        tx_id = request.args.get( "tx" )
    else:
        tx_id = request.form.get( "tx" )
    tx_id = str( tx_id )
    session_id = request.form.get( "session_id" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT preimage from preimages WHERE transaction_id = '" + tx_id + "'" )
    preimage = cur.fetchone()
    preimage = preimage[ 0 ]
    con.close()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    if ( tdata[ "status" ] == "funds received" ):
        return ""
    status = "funds received"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    seller = tdata[ "seller" ]
    user = lookupuser( session_id )
    if ( seller == "" ):
        seller = -1
    if ( seller == user and tdata[ "status" ] == "goods received" ):
        con = sqlite3.connect( "lnescrow.db" )
        cur = con.cursor()
        cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
        con.commit()
        con.close()
    if ( seller == user and ( tdata[ "status" ] == "goods received" ) or ( tdata[ "status" ] == "funds received" ) ):
        return preimage
    else:
        return "nice try!"

@app.route( '/getpreimage/v2', methods=[ 'POST', 'GET' ] )
@app.route( '/getpreimage/v2/', methods=[ 'POST', 'GET' ] )
def getpreimagev2():
    tx_id = request.json[ "tx" ]
    tx_id = str( tx_id )
    session_id = request.json[ "session_id" ]
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT preimage from preimages WHERE transaction_id = '" + tx_id + "'" )
    preimage = cur.fetchone()
    preimage = preimage[ 0 ]
    con.close()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT transaction_data from transactions WHERE transaction_id = '" + tx_id + "'" )
    transaction = cur.fetchone()
    transaction = transaction[ 0 ]
    tdata = json.loads( transaction )
    con.close()
    if ( tdata[ "status" ] == "funds received" ):
        return ""
    status = "funds received"
    transaction = {
        "id": tdata[ "id" ],
        "shipping_link": tdata[ "shipping_link" ],
        "created": tdata[ "created" ],
        "expires": tdata[ "expires" ],
        "buyer": tdata[ "buyer" ],
        "buyer_email": tdata[ "buyer_email" ],
        "seller": tdata[ "seller" ],
        "goods_or_services": tdata[ "goods_or_services" ],
        "title": tdata[ "title" ],
        "description": tdata[ "description" ],
        "fee_payer": tdata[ "fee_payer" ],
        "amount": tdata[ "amount" ],
        "status": status,
        "invoice": tdata[ "invoice" ],
        "pmthash": tdata[ "pmthash" ],
    }
    tjson = json.dumps( transaction )
    seller = tdata[ "seller" ]
    user = lookupuser( session_id )
    if ( seller == "" ):
        seller = -1
    if ( seller == user and tdata[ "status" ] == "goods received" ):
        con = sqlite3.connect( "lnescrow.db" )
        cur = con.cursor()
        cur.execute( "UPDATE transactions SET transaction_data = :transaction_data WHERE transaction_id = :transaction_id",
                       { "transaction_data": tjson, "transaction_id": tx_id } )
        con.commit()
        con.close()
    if ( seller == user and ( tdata[ "status" ] == "goods received" ) or ( tdata[ "status" ] == "funds received" ) ):
        returnable = {
            "status": "success",
            "preimage": preimage,
            "data": {
                "id": str( transaction[ "id" ] ),
                "shipping_link": str( transaction[ "shipping_link" ] ),
                "created": str( transaction[ "created" ] ),
                "expires": str( transaction[ "expires" ] ),
                "buyer": str( transaction[ "buyer" ] ),
                "buyer_email": str( transaction[ "buyer_email" ] ),
                "seller": str( transaction[ "seller" ] ),
                "goods_or_services": str( transaction[ "goods_or_services" ] ),
                "title": str( transaction[ "title" ] ),
                "description": str( transaction[ "description" ] ),
                "fee_payer": str( transaction[ "fee_payer" ] ),
                "amount": str( transaction[ "amount" ] ),
                "status": str( transaction[ "status" ] ),
                "pmthash": str( transaction[ "pmthash" ] ),
            }
        }
        return json.dumps( returnable )
    else:
        return "nice try!"

@app.route( "/" )
def root():
    return render_template( "main.html" )

@app.route( "/main.html" )
def redirecthome():
    return '<html><body><script>window.location.href = "/";</script></body></html>'

@app.route( "/about.html" )
def about():
    return render_template( "about.html" )

@app.route( "/faq.html" )
def faq():
    return render_template( "faq.html" )

@app.route( "/developers.html" )
def developers():
    return render_template( "developers.html" )

@app.route( "/contact-us.html" )
def contact():
    return render_template( "contact-us.html" )

@app.route( "/log-in.html" )
def login():
    return render_template( "log-in.html" )

@app.route( "/sign-up.html" )
def signup():
    return render_template( "sign-up.html" )

@app.route( "/dashboard.html", methods=[ 'GET' ] )
def dashboard():
    return render_template( "dashboard.html" )

@app.route( "/seller-info.html" )
def sellerinfo():
    return render_template( "seller-info.html" )

@app.route( "/details-page.html" )
def detailspage():
    return render_template( "details-page-buyer.html" )

@app.route( "/buyer-payment.html" )
def buyerpayment():
    return render_template( "buyer-payment.html" )

@app.route( "/seller-payment.html" )
def sellerpayment():
    return render_template( "seller-payment.html" )

@app.route( "/seller-confirmation.html" )
def sellerconfirmation():
    return render_template( "seller-confirmation.html" )

@app.route( "/seller-success.html" )
def sellersuccess():
    return render_template( "seller-success.html" )

@app.route( "/buyer-confirmation.html" )
def buyerconfirmation():
    return render_template( "buyer-confirmation.html" )

@app.route( "/buyer-success.html" )
def buyersuccess():
    return render_template( "buyer-success.html" )

@app.route( "/qr.js" )
def qrjs():
    return render_template( "qr.js" )

@app.route( "/lastpage-seller.html" )
def lastpageseller():
    return render_template( "lastpage-seller.html" )

@app.route( "/lastpage-buyer.html" )
def lastpagebuyer():
    return render_template( "lastpage-buyer.html" )

@app.route( "/check-transaction-status.html" )
def checktxstatus():
    return render_template( "check-transaction-status.html" )

@app.route( "/contract-funded.html" )
def contractfunded():
    return render_template( "contract-funded.html" )

@app.route( "/goods-sent.html" )
def goodssentpage():
    return render_template( "goods-sent.html" )

@app.route( "/img/acf4ee7136a15d6d84f05bc4658227e3.png" )
def logoimg():
    return send_file( "static/img/acf4ee7136a15d6d84f05bc4658227e3.png" )

@app.route( "/testing1" )
def makepdf():
# importing modules
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib import colors

# initializing variables with values
    fileName = 'sample.pdf'
    documentTitle = 'sample'
    title = 'LightningEscrow Receipt'
    subTitle = 'Your product is delivered'
    textLines = [
        'This receipt acknowledges the payment made by',
        'supertestnet@gmail.com in the amount of',
        '5000 sats for the item purchased in the',
        'transaction called Choky Milk.',
    ]
    image = 'static/img/acf4ee7136a15d6d84f05bc4658227e3.png'

# creating a pdf object
    pdf = canvas.Canvas(fileName)

# setting the title of the document
    pdf.setTitle(documentTitle)

# registering a external font in python
#    pdfmetrics.registerFont(
#        TTFont('abc', 'static/fonts/sakbunderan.ttf')
#    )

# drawing a letterhead image at the
# specified (x.y) position
    pdf.drawImage(image, 265, 745, 50, 50, mask="auto")

# creating the title by setting it's font
# and putting it on the canvas
    pdf.setFont('Helvetica', 36)
    pdf.drawCentredString(290, 700, title )

# creating the subtitle by setting it's font,
# colour and putting it on the canvas
    pdf.setFillColorRGB(0, 0, 255)
    pdf.setFont("Courier-Bold", 24)
    pdf.drawCentredString(290, 670, subTitle)

# drawing a line
    pdf.line(30, 650, 550, 650)

# creating a multiline text using
# textline and for loop
    text = pdf.beginText(40, 620)
    text.setFont("Courier", 18)
    text.setFillColor(colors.black)
    for line in textLines:
        text.textLine(line)
    pdf.drawText(text)

# saving the pdf
    pdf.save()

    return ""

@app.route( "/sample.pdf" )
def sendpdf():
    return send_file( "sample.pdf" )

@app.route( "/.well-known/lnurlp/<username>" )
def prelnaddy(username):
    prelnaddy = {
        "callback":"https://app.lightningescrow.io/api/lnurlp/" + username + "/pay",
        "minSendable":1000,
        "maxSendable":9007199254740991,
        "metadata":"[[\"text/plain\",\"paying " + username + " on lightningescrow.io\"]]",
        "tag":"payRequest"
    }
    prelnaddy = json.dumps( prelnaddy )
    return prelnaddy

@app.route( "/api/lnurlp/<username>/pay" )
def lnaddy(username):
    lnerror = {
        "status":"ERROR",
        "reason":"amount must be >=1000 msats"
    }
    lnerror = json.dumps( lnerror )
    lnaddress = {
        "pr": "lnbc5u1pslal9lpp55ap25nz5znmlyye8mly29pr08h69t6x8vzr90jfzfy2096hhq9lqdq8w3jhxaqxqyjw5qcqpjsp5e606rg8efvpp2d20waajw3ytlnza83rlk36wjxes6xpp60pm293srzjqwwpe4vgx9ngul7jhz0l92t0ap5ywr3kp6qn7l70ylchqd6wvy2azz5v5qqq23gqqyqqqqlgqqqqqqgq9q9qy9qsqknxwndjfdngcqqvtjjatzt6lvwdkv42swdaj2gvec7u27x9fnu63xumxjmfc4p94w7zj9dqln2f74q3zdv3g9hh5u5kd35zr4ahvdsqpxztg7a"
    }
    lnaddress = json.dumps( lnaddress )
    if ( not request.args.get( "amount" ) ):
        lnaddress = lnerror
    return lnaddress

@app.route( "/extend-session/", methods=[ "POST", "GET" ] )
def extendsessionkey():
    session_id = request.args.get( "session_id" )
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user, session_id, expiry from sessions WHERE session_id = '" + session_id + "'" )
    session = cur.fetchone()
    sjson = json.dumps( session )
    con.close()
    longexpiry = 2176860314
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "UPDATE sessions SET expiry = :longexpiry WHERE session_id = :session_id",
                       { "longexpiry": str( longexpiry ), "session_id": session_id } )
    con.commit()
    con = sqlite3.connect( "lnescrow.db" )
    cur = con.cursor()
    cur.execute( "SELECT user, session_id, expiry from sessions WHERE session_id = '" + session_id + "'" )
    session = cur.fetchone()
    sjson = json.dumps( session )
    con.close()
    newexpiry = session[ 2 ]
    status = {
        "status": "success",
        "user": session[ 0 ],
        "session_id": session[ 1 ],
        "expiry": newexpiry
    }
    return status

@app.route('/favicon.ico')
def favicon():
    return send_from_directory( os.path.join( app.root_path, 'static' ),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon' )

if __name__ == "__main__":
    app.run( port=1234 )
