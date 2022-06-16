# You need these libraries

```
<script src="https://bundle.run/ecies-lite@1.1.3"></script>
<script src="https://bundle.run/buffer@6.0.3"></script>
<script src="https://bitcoincore.tech/apps/bitcoinjs-ui/lib/bitcoinjs-lib.js"></script>
<script src="https://bundle.run/noble-secp256k1@1.2.14"></script>
```

# Set oracle

```
function makeUser( authkey ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               sessionStorage[ "session_id" ] = JSON.parse( xhr.responseText )[ "session" ];
                               sessionStorage[ "oracle" ] = JSON.parse( xhr.responseText )[ "id" ];
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "authkey": authkey
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/setuser/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

var rand = new Uint8Array( 32 );
var authkey = buffer.Buffer.from( window.crypto.getRandomValues( rand ) ).toString( "hex" );
sessionStorage[ "authkey" ] = authkey;
makeUser( authkey );
```

# Log oracle in

```
function logUserIn( authkey ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                               sessionStorage[ "session_id" ] = JSON.parse( xhr.responseText )[ "session" ];
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "authkey": authkey
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/login/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

var authkey = sessionStorage[ "authkey" ];
logUserIn( authkey );
```

# Get oracle

```
function getUser( user_id ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            xhr.open( 'GET', 'https://app.lightningescrow.io/getbluser/?user=' + user_id );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send();
}

var user = sessionStorage[ "oracle" ];
getUser( user );
```

# Get all oracle transactions

```
function getAllUserTxs( session_id ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/getallusertxs/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

var session_id = sessionStorage[ "session_id" ];
getAllUserTxs( session_id );
```

# Get a specific transaction

```
function getOneTx( session_id, tx_id ) {
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "tx": tx_id,
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/gettx/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

var session_id = sessionStorage[ "session_id" ];
var tx_id = "0";
getOneTx( session_id, tx_id );
```

# Create transaction

```
function setTx( session_id, escrowpubkey, commspubkey, escrowprivkey, fee_payer, amount ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "seller_pubkey": escrowpubkey,
                    "seller_comms_pubkey": commspubkey,
                    "seller_privkey": escrowprivkey,
                    "fee_payer": fee_payer,
                    "amount": amount,
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/setbltx/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

function makeSmallPrivkey() {
        var rand = new Uint8Array( 32 );
        var privkey = buffer.Buffer.from( window.crypto.getRandomValues( rand ) ).toString( "hex" );
        if ( privkey.substring( 0, 1 ) != '0' || privkey.substring( 1, 2 ) != '0' ) {
                return makeSmallPrivkey()
        }
        return privkey;
}

var session_id = sessionStorage[ "session_id" ];
var escrowpubkey = "";
var commspubkey = "";
var escrowprivkey = "";
var fee_payer = "buyer";
var amount = 5000;
var commsprivkey = "";
var escrowprivkey = makeSmallPrivkey();
sessionStorage[ "escrowprivkey" ] = escrowprivkey;
escrowpubkey = nobleSecp256k1.getPublicKey( escrowprivkey, true );
commsprivkey = makeSmallPrivkey();
sessionStorage[ "commsprivkey" ] = commsprivkey;
var commspubkey = nobleSecp256k1.getPublicKey( commsprivkey, true );
var amount = 5000;
setTx( session_id, escrowpubkey, commspubkey, escrowprivkey, fee_payer, amount );
```

# Set buyer

```
var session_id = sessionStorage[ "session_id" ];
var seller_comms_pubkey = "03fe9aa42450034b592680ccdc7fa0167912570bd11c6cd8ad601451f521871355";
var seller_pubkey = "02d07c9074b3945b7a22915b0590445b1ccd76dbd5c0db64b3834231b66995c35b";
var escrow_pubkey = "0215b859952a793b7f1b94e75b6adf87697654e8de5d37ea47830f42bc7595a533";
var tx_id = "18";

function acceptContract( pubkey, eprivkey, tx_id, combined_pubkey ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                               sessionStorage[ "escrow_privkey" ] = JSON.parse( xhr.responseText )[ "escrow_privkey" ];
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "pubkey": pubkey,
                    "eprivkey": eprivkey,
                    "tx": tx_id,
                    "combined_pubkey": combined_pubkey,
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/setbuyer/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

function computeAddress( node ) {
            return bitcoinjs.payments.p2wpkh({ pubkey: node.publicKey, network: bitcoinjs.networks.mainnet }).address;
    }

function makeSmallPrivkey() {
        var rand = new Uint8Array( 32 );
        var privkey = buffer.Buffer.from( window.crypto.getRandomValues( rand ) ).toString( "hex" );
        if ( privkey.substring( 0, 1 ) != '0' || privkey.substring( 1, 2 ) != '0' ) {
                return makeSmallPrivkey()
        }
        return privkey;
}

var privkey = makeSmallPrivkey();
sessionStorage[ "buyer_privkey" ] = privkey;
var emsg = eciesLite.encrypt( buffer.Buffer.from( seller_comms_pubkey, "hex" ), privkey );
var eb64 = btoa( buffer.Buffer.from( JSON.stringify( emsg ), "utf-8" ) );
var pubkey = nobleSecp256k1.getPublicKey( privkey, true );
var combined_pubkey = bitcoinjs.ECPair.fromPublicKey( buffer.Buffer.from( nobleSecp256k1.Point.fromHex( seller_pubkey ).add( nobleSecp256k1.Point.fromHex( pubkey ).add( nobleSecp256k1.Point.fromHex( escrow_pubkey ) ) ).toHex(), "hex" ) ).publicKey.toString( "hex" );
sessionStorage[ "combopubkey" ] = combined_pubkey;
sessionStorage[ "escrowaddress" ] = computeAddress( bitcoinjs.ECPair.fromPublicKey( buffer.Buffer.from( nobleSecp256k1.Point.fromHex( combined_pubkey ).toHex(), "hex" ) ) );
acceptContract( pubkey, eb64, tx_id, combined_pubkey );
```

# Seller ack

```
var session_id = sessionStorage[ "session_id" ];
var seller_comms_privkey = sessionStorage[ "comms_privkey" ];
var tx_id = "18";
var emsg = "eyJlcGsiOnsidHlwZSI6IkJ1ZmZlciIsImRhdGEiOls0LDcwLDI4LDIwMCwxNzAsMjI4LDIxMyw4Niw4OSw4Niw2Miw4MywxOCwxMyw4LDEwNSwxNDAsMTU3LDUsNDMsMTkwLDEyMSwxMDIsNzEsMTU0LDIzNywxMywxMDQsNTksMTAyLDE3LDE1MywxNywyMjcsMTU1LDIwNSw2MCwxMTksMTM4LDE5MywyMzUsMjQsMjEzLDEwOSwxMjMsMjI3LDM2LDIzNiwxMTksMjM2LDQ5LDE3NSwxNDAsNDMsMjAwLDI1MywyMjYsMTM3LDMsMSwxMDYsMjUsMjksMTMwLDI2XX0sIml2Ijp7InR5cGUiOiJCdWZmZXIiLCJkYXRhIjpbMjEsMTc2LDI0NiwxMzgsMTQ3LDE1MywyMSwyMTgsMTYsMjMsMTk0LDIxOCwxODAsMzAsMCwyNF19LCJjdCI6eyJ0eXBlIjoiQnVmZmVyIiwiZGF0YSI6WzE5NSwxNDAsNCwxNCwyMzUsMTE0LDIxNywxMDEsNTUsMTA5LDE3OSw1NCwyMjcsMjI5LDIxMiw5NSwxMzcsODYsMTA5LDE4MiwyMDEsMTUwLDE2MSwxNzgsMjExLDgxLDc3LDEzNCwxNjQsMjA3LDM1LDExMiw3OCwxMCwxMDUsMTk2LDk0LDEzLDc0LDI1NSwxNjgsMjAxLDE4MywyMzMsMTE5LDEwMSwxNDksMTY2LDExLDEyNSwxMTMsMTkwLDEyMCwzOCw0NSwxNzEsMTUzLDYzLDE4NywyMTEsMTU3LDIyMywxNTEsMjIzLDIyMiwxNSwyMDUsNTMsMTQ5LDI0NCw5NCwzOSw0Myw5Niw2MiwyMDEsMTQ0LDc3LDczLDEwXX0sIm1hYyI6eyJ0eXBlIjoiQnVmZmVyIiwiZGF0YSI6WzE1NCw0MSw1NywyMzAsMTE1LDE5OCw1MCwzMiw5MCw2MiwyMDIsMjEsNzksMTA0LDc3LDI1NCwyNTIsMTgsODIsOTksMTQ4LDE3NywxMzIsMjQ2LDE5Nyw0NSwxNDMsMTgsMTMyLDE4Niw2OCw1M119fQ==";

var getJson = new Promise( function( resolve, reject ) {
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               var json = JSON.parse( xhr.responseText );
                               resolve( json );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "tx": tx_id,
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/gettx/v3/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
});

getJson
  .then(function( result ) {
    console.log( "result:", result );
    escrow_pubkey = result[ "escrow_pubkey" ];
    console.log( "escrow_pubkey:", escrow_pubkey );
    supposed_combined_pubkey = result[ "combined_pubkey" ];
    console.log( "supposed_combined_pubkey:", supposed_combined_pubkey );
    emsg = result[ "buyer_encrypted_privkey" ];
    console.log( "emsg:", emsg );
            var omsg = JSON.parse( atob( emsg ) );
    console.log( "omsg:", omsg );
            var nmsg = {
                "epk": buffer.Buffer.from( omsg.epk ),
                "iv": buffer.Buffer.from( omsg.iv ),
                "ct": buffer.Buffer.from( omsg.ct ),
                "mac": buffer.Buffer.from( omsg.mac )
            }
    console.log( "nmsg:", nmsg );
            var seller_comms_privkey = sessionStorage[ "commsprivkey" ];
            var dmsg = eciesLite.decrypt( buffer.Buffer.from( seller_comms_privkey, "hex" ), nmsg );
    console.log( "dmsg:", dmsg );
            var buyer_privkey = dmsg.toString();
            console.log( "buyer privkey", buyer_privkey );
            sessionStorage[ "buyer_privkey" ] = buyer_privkey;
            var seller_pubkey = nobleSecp256k1.getPublicKey( sessionStorage[ "escrowprivkey" ], true );
            console.log( "seller pubkey", seller_pubkey );
            var buyer_pubkey = nobleSecp256k1.getPublicKey( buyer_privkey, true );
            console.log( "buyer pubkey", buyer_pubkey );
            console.log( "escrow pubkey", escrow_pubkey );
            var actual_combined_pubkey = bitcoinjs.ECPair.fromPublicKey( buffer.Buffer.from( nobleSecp256k1.Point.fromHex( seller_pubkey ).add( nobleSecp256k1.Point.fromHex( buyer_pubkey ).add( nobleSecp256k1.Point.fromHex( escrow_pubkey ) ) ).toHex(), "hex" ) ).publicKey.toString( "hex" );
            console.log( "supposed combined pubkey", supposed_combined_pubkey );
            console.log( "actual combined pubkey", actual_combined_pubkey );
            console.log( "are they the same?", actual_combined_pubkey == supposed_combined_pubkey );
            if ( actual_combined_pubkey == supposed_combined_pubkey ) {
                    sessionStorage[ "combopubkey" ] = actual_combined_pubkey;
                    sellerAck( sessionStorage[ "session_id" ], tx_id );
            }
  });

function sellerAck( session_id, tx_id ) {               
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "tx": tx_id,
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/sellerack/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}
```

# Set winner

```
var session_id = sessionStorage[ "session_id" ];
var tx_id = "18";
winner = "buyer";

function makeWinner( session_id, tx_id, winner ) {
            var xhr = new XMLHttpRequest();
            xhr.onload = () => {
                       if (xhr.status >= 200 && xhr.status < 300) {
                               console.log( xhr.responseText );
                    } else {
                                alert( "Your request was not processed correctly, please try again." );
                    }
            }
            var json = {
                    "session_id": session_id,
                    "tx": tx_id,
                        "winner": winner
            };
            xhr.open( 'POST', 'https://app.lightningescrow.io/getblkey/' );
            xhr.setRequestHeader( 'Content-Type', 'application/json' );
            xhr.send( JSON.stringify( json ) );
}

makeWinner( session_id, tx_id, winner );
```

# Use this script to get the private key to the address

```
var seller_privkey = "1208e93de5b4f446528032b8ce2ca771514b454d94aecb480ae9aad805949ac5";
var buyer_privkey = "00075a1040fd0d4bf74d452d40252a6e4ac7db79f0eac0337678228c2f6c789d";
var escrow_privkey = "00d8d369f34be6f7552bfcc3ef9d67a10c17483343df4668028af780e31b7485";
var comboprivkey = ( ( BigInt( "0x" + seller_privkey ) + BigInt( "0x" + buyer_privkey ) + BigInt( "0x" + escrow_privkey ) ) % BigInt( "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f" ) ).toString( 16 );
var keypadder = "0000000000000000000000000000000000000000000000000000000000000000";
keypadder += comboprivkey;
comboprivkey = keypadder.slice( -64 );
var combopubkey = bitcoinjs.ECPair.fromPublicKey( buffer.Buffer.from( nobleSecp256k1.Point.fromPrivateKey( comboprivkey ).toHex(), "hex" ) ).publicKey.toString( "hex" );
console.log( "public key:", combopubkey );
console.log( "private key:", comboprivkey );
```

# Spend the money in the address

To spend the money in the address you need to use a library like bitcoinjs. The steps to create a spend transaction are not documented here, try this link:

[https://bitcoinjs-guide.bitcoin-studio.com/bitcoinjs-guide/v5/part-two-pay-to-public-key-hash/p2wpkh/p2wpkh_spend_1_1.html](https://bitcoinjs-guide.bitcoin-studio.com/bitcoinjs-guide/v5/part-two-pay-to-public-key-hash/p2wpkh/p2wpkh_spend_1_1.html)
