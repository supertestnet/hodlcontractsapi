# Documentation for the api endpoints formerly available at lightningescrow.io

# Video demo

[![](https://i.ibb.co/0FgRK0m/lnescrow-api-demo.png)](https://www.youtube.com/watch?v=OufAyoxfH9M)

# Create user

Endpoint: https://app.lightningescrow.io/setuser/v2/

What it expects: a json encoded post request with these contents:
```
{
    "email": <string an_email_address>,
    "password": <string a_secure_password>
}
```
What it returns:
```
{
    "status": "success",
    "session": <string session_key>,
    "id": <string user_id>,
    "expiry": <string unix_timestamp>
}
```
Notes:

The setuser endpoint creates a new user with the email and password passed in the json if a user with the given email and password does not already exist. The password is not stored on the server but is instead salted and then hashed. The salted hash is stored on the server. Later login attempts take an email and password as input from the user, salt the password and then hash it, and compare the salted hash to the string stored in our database for that username. If there is a match, the user is allowed to log in.

To protect user privacy, a fake email may be entered in as the user’s email. Putting a fake email into this field is also desirable if you do not wish Lightning Escrow to send automated emails to your users notifying them of the next steps they should take to complete their transactions. Also note that it is perfectly fine for developers to create one account for their whole service rather than individual accounts for each of their users. A service can then act as both buyer and seller for all transactions involving their users, calling the api to settle or cancel payments programmatically without taking custody of user funds. The only thing really needed from a seller is an invoice, and the only thing really needed from a buyer is an attempt to pay that invoice.

There is a key/value pair in the returned json called session. Its value is a session key. Session keys are used in all queries other than “create user” and “login” to authenticate that a given user is authorized to make a particular query. When a session key is generated (either by creating a user or logging in), their session key is stored in our database along with the user’s id number. Whoever passes the session key in any other query is assumed to be the user whose id number is next to that session key in our database. That user can create and update contracts associated with their own user id. Thus, whoever has the session key can create and update contracts associated with that user id. Session keys expire after 14 days but can be extended using the “extend session” endpoint described in another section.

There is a key/value pair in the returned json called id. Its value is the id number of the user who was just created.

There is a key/value pair in the returned json called expiry. Its value is a unix timestamp at which time our server will stop responding to the current session key. After that point, a new one will have to be generated to keep using our api.

Sample script (vanilla js):
```
                var email = "johnsmith@example.com";
                var password = "hunter12";
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your signup was not processed correctly, please try again." );
                    }
                }
                var json = {
                    "email": email,
                    "password": password
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/setuser/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Get session key (a.k.a. log in)

Endpoint: https://app.lightningescrow.io/login/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "email": <string an_email_address>,
    "password": <string a_secure_password>
}
```
What it returns:
```
{
    "status": "success",
    "session": <string session_key>,
    "id": <string user_id>,
    "expiry": <string unix_timestamp>
}
```
Notes:

The login endpoint verifies that the password passed in the json, when hashed and salted, matches the password in our database that corresponds with the email passed in the json. If so, it returns a session key which the user can use in subsequent queries to create and update contracts.

There is a key/value pair in the returned json called session. Its value is a session key. Session keys are used in all queries other than “create user” and “login” to authenticate that a given user is authorized to make a particular query. When a session key is generated (either by creating a user or logging in), their session key is stored in our database along with the user’s id number. Whoever passes the session key in any other query is assumed to be the user whose id number is next to that session key in our database. That user can create and update contracts associated with their own user id. Thus, whoever has the session key can create and update contracts associated with that user id. Session keys expire after 14 days but can be extended using the “extend session” endpoint described in another section.

There is a key/value pair in the returned json called id. Its value is the id number of the user who just logged in.

There is a key/value pair in the returned json called expiry. Its value is a unix timestamp at which time our server will stop responding to the current session key. After that point, a new one will have to be generated to keep using our api.

Sample script (vanilla js):
```
                var email = "johnsmith@example.com";
                var password = "hunter12";
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your signup was not processed correctly, please try again." );
                    }
                }
                var json = {
                    "email": email,
                    "password": password
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/login/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Extend session key into api key

Endpoint: https://app.lightningescrow.io/extend-session/?session_id=<some_session_id>

What it expects: a GET request with the user’s session key submitted as the value of the session_key parameter.

What it returns:
```
{
    "expiry":<string unix_timestamp>,
    "session_id":<string session_key>,
    "status":"success",
    "user":<string user_id>
}
```
Notes:

Developers who wish their session keys would last longer than 2 weeks may convert them to an api key by this method. Session keys which are extended using this endpoint do not expire until the year 2038. Developers can then use them to authenticate with our server and create/update contracts til the cows come home without worrying that they’ll get “logged out” soon and need a new session key.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your session extension was not processed correctly, please try again." );
                    }
                }
                xhr.open( 'GET', 'https://app.lightningescrow.io/extend-session/?session_id=' + session_id );
                xhr.send();
```
# Create transaction

Endpoint: https://app.lightningescrow.io/settx/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "buyer_email": <string an_email_address>,
    "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
    "title": <string a_title_for_this_transaction>,
    "description": <string a_description_for_this_transaction>,
    "fee_payer": <string the_single_word_buyer_or_the_single_word_seller>,
    "amount": <integer amount_to_be_paid_in_sats>
}
```
What it returns:
```
{
    "status": "success",
    "data": {
        "status": "needs invoice", 
        "expires": <integer timestamp_of_when_the_offer_expires>, 
        "description": <string description_of_transaction_derived_from_input>, 
        "buyer_email": <string email_of_the_buyer>, 
        "fee_payer": <string single_word_buyer_or_seller>, 
        "buyer": "", 
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>, 
        "id": <string unique_id_number_of_transaction>, 
        "shipping_link": "", 
        "title": <string title_of_transaction_derived_from_input>, 
        "created": <integer timestamp_of_when_the_offer_was_created>, 
        "seller": <string id_number_of_seller_derived_from_session_key>, 
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>, 
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

To protect user privacy, a fake email may be entered in as the buyer’s email. Putting a fake email into this field is also desirable if you do not wish Lightning Escrow to send automated emails to your users notifying them of the next steps they should take to complete their transactions.

The most important item in the returned json is the transaction id, which will be used in subsequent queries to update this transaction and check its status as various parts of the contract interaction are completed.

The second most important item in the returned json is the pmthash, which must be used in the next step where an invoice is created with that payment hash. Lightning Escrow keeps a copy of the preimage to that payment hash and will reveal it to the money recipient later if they are supposed to receive the money.

It is also important to note that the "expires" field always assumes that a contract's duration is 2 weeks from the time of its creation. This value may be customizable in a future update. The expires field does ___NOT___ correspond to the lightning invoice's minimum locktime requirement. Developers must currently infer the lightning invoice's minimum locktime requirement by decoding the invoice themselves. A future update may display add a field that indicates what an invoice requires for a minimum locktime. This is very important because when the locktime of a lightning payment expires, that payment automatically cancels. If that happens, there is no recourse for the seller, even if he already shipped out the goods. Since the value of the minimum invoice locktime is independent of the transaction expiry, developers must not assume that they can wait to decide how to settle a transaction til right before it expires. That would be unsafe because the lightning payment at stake in the transaction may automatically time out (and thus cancel) long before the transaction reaches its expiration date.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var buyer_email = "garethwilson@example.com";
                var goods_or_services = "goods";
                var title = "Pizza for dietz";
                var description = "Large pepperoni with a side of snakes";
                var fee_payer = "buyer";
                var amount = 5000;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your transaction was not created, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "buyer_email": buyer_email,
                    "goods_or_services": goods_or_services,
                    "title": title,
                    "description": description,
                    "fee_payer": fee_payer,
                    "amount": amount,
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/settx/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Get all user transactions

Endpoint: https://app.lightningescrow.io/getallusertxs/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>
}
```
What it returns:
```
[
    {
        "status": <string status_of_this_transaction>, 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }, 
    ..., 
    {
        "status": <string status_of_this_transaction>, 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
]
```
Notes:

The shipping link field is not currently used but may play a role in a future update.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                
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
                xhr.open( 'POST', 'https://app.lightningescrow.io/getallusertxs/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Get a single transaction

Endpoint: https://app.lightningescrow.io/gettx/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": <string a_transaction_id_provided_by_lightning_escrow_in_previous_step>
}
```
What it returns:
```
{
    "status": <string status_of_this_transaction>, 
    "expires": <string timestamp_of_when_the_offer_expires>,
    "description": <string description_of_transaction_derived_from_input>,
    "buyer_email": <string email_of_the_buyer>,
    "invoice": <string invoice_derived_from_input>,
    "fee_payer": <string single_word_buyer_or_seller>,
    "buyer": <string id_number_of_buyer>,
    "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
    "id": <string id_number,
    "shipping_link": "",
    "title": <string title_of_transaction_derived_from_input>,
    "created": <string timestamp_of_when_the_offer_was_created>,
    "seller": <string id_number_of_seller_derived_from_session_key>,
    "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
    "amount": <string quantity_of_sats_to_be_paid_by_buyer>
} 
```
Notes:

The values for expires, id, buyer, seller, and created are sometimes integers instead of strings.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
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
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/gettx/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Create invoice

Endpoint: https://app.lightningescrow.io/setinvoice/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "invoice": <string invoice_with_pmthash_provided_by_lightning_escrow_in_previous_step>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "data": { 
        "status": "needs paid", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": "",
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string unique_id_number_of_transaction>,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

A transaction is not ready for the buyer to interact with until an invoice is submitted by the seller. Nonetheless, creating an invoice is done separately from creating the transaction so that developers have the option of asking users for an invoice on a separate page from where they ask them to initiate a transaction. This may be helpful in scenarios where developers want to give users time to go get a wallet that supports the lightning escrow protocol but still collect information about their transaction in the meantime. It is also worth noting that, when Lightning Escrow begins charging for service at some point in the future, there may sometimes be a step before the "create invoice" step where the seller is asked to pay an invoice to Lightning Escrow for the service we provide. We may also add a feature whereby the seller has to put up some collateral in a lightning-based fidelity bond as a deterrant to opening disputes unnecessarily. Opening a dispute would then mean withdrawing your right to recover that collateral -- Lighnting Escrow would keep it instead.

When an invoice is added to a transaction, an email is fired off to the buyer’s email address notifying them that someone wants to transact with them. Automatic emails are also sent out at every other step of this process.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var invoice = "lnbc50u1p3z86a3pp5e60amepkjnt27xz8a3qfl9z87uncanlrxsppu656stzawuhv05ksdqqcqzpgxq9pyagqsp5ts5lg0wl32ttf42ru732c8n5pnmpysd49nvgwtnqakmemu3ujn8s9qyyssqagkjxkdpnp4k93gxla37muursw379tqs8aeu4ka8n2wp0jwzh2trepv8nn5rptrgjl9hr7vaats240xkd3kdp9qyl8x5wxru90fp3hgqd2lqsz";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your invoice was not processed successfully, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "invoice": invoice,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/setinvoice/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Set Buyer

Endpoint: https://app.lightningescrow.io/login/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "email": <string an_email_address>,
    "password": <string a_secure_password>,
    "tx": <string a_transaction_id_provided_by_lightning_escrow_in_previous_step>
}
```
What it returns:
```
{
    "status": "success",
    "session": <string session_key>,
    "id": <string user_id>,
    "expiry": <string unix_timestamp>
}
```
Notes:

When setting a buyer, the procedure is the same as it is for logging in (you can also use the “sign up” endpoint with the same parameters), except you must also provide a transaction id number. The user who logs in (or gets created) using this endpoint with a transaction id number automatically becomes the buyer for this transaction, unless a buyer already exists for this transaction. It is also worth noting that, when Lightning Escrow begins charging for service at some point in the future, there may sometimes be a step before, after, or during the "Set Buyer" step where the buyer is asked to pay an invoice to Lightning Escrow for the service we provide. We may also add a feature whereby the buyer has to put up some collateral in a lightning-based fidelity bond as a deterrant to opening disputes unnecessarily. Opening a dispute would then mean withdrawing your right to recover that collateral -- Lighnting Escrow would keep it instead.

Sample script (vanilla js):
```
                var email = "johnsmith@example.com";
                var password = "password123";
                var tx = 35;

                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your signup was not processed correctly, please try again." );
                    }
                }
                var json = {
                    "email": email,
                    "password": password,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/login/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Buyer claims the contract is funded

Endpoint: https://app.lightningescrow.io/buyerpaid/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "data": { 
        "status": "claims paid", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

This step should be optional though I haven’t actually tested if the procedure works without it. At lightning escrow we assume that users may act asynchronously and if one pays, the other user might check if they paid a day later. To facilitate this, we ask the buyer to tell us they paid so that we can inform the seller via email that they should check if their node detected the payment attempt. Services which automate the status checking (such as by using a macaroon to automatically check the seller’s node for a payment status) may not need this step. You need not ask the buyer to say they paid if you can automatically check whether they paid (e.g. by querying the seller’s node).

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your payment claim was not received, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/buyerpaid/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Seller confirms contract funded

Endpoint: https://app.lightningescrow.io/confirmpayment/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "data": { 
        "status": "paid", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

[None at this time]

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your update about the contract being funded was not received, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/confirmpayment/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Seller confirms goods sent

Endpoint: https://app.lightningescrow.io/goodssent/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "data": { 
        "status": "goods sent", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

[None at this time]

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your claim that the goods were sent was not received, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/goodssent/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Buyer confirms goods received

Endpoint: https://app.lightningescrow.io/goodsreceived/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "data": { 
        "status": "goods received", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

[None at this time]

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your claim that the goods were received was not received, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/goodsreceived/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
# Seller requests preimage

Endpoint: https://app.lightningescrow.io/getpreimage/v2/

What it expects: a json encoded POST request with these contents:
```
{
    "session_id": <string session_key>,
    "tx": "<string transaction_id_number_provided_by_lightning_escrow_in_previous_step>"
}
```
What it returns:
```
{
    "status": "success", 
    "preimage": <string a_preimage_generated_earlier_by_lightning_escrow>,
    "data": { 
        "status": "funds received", 
        "expires": <string timestamp_of_when_the_offer_expires>,
        "description": <string description_of_transaction_derived_from_input>,
        "buyer_email": <string email_of_the_buyer>,
        "invoice": <string invoice_derived_from_input>,
        "fee_payer": <string single_word_buyer_or_seller>,
        "buyer": <string id_number_of_buyer>,
        "goods_or_services": <string the_single_word_goods_or_the_single_word_services>,
        "id": <string id_number,
        "shipping_link": "",
        "title": <string title_of_transaction_derived_from_input>,
        "created": <string timestamp_of_when_the_offer_was_created>,
        "seller": <string id_number_of_seller_derived_from_session_key>,
        "pmthash": <string payment_hash_supplied_by_lightning_escrow>,
        "amount": <string quantity_of_sats_to_be_paid_by_buyer>
    }
}
```
Notes:

The seller can use the preimage to settle the lightning invoice they created in a previous step. If the preimage is not disclosed to them, the payment will time out when it reaches the blockheight of its absolute locktime value.

Sample script (vanilla js):
```
                var session_id = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
                var tx = 35;
                
                var xhr = new XMLHttpRequest();
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log( xhr.responseText );
                    } else {
                        alert( "Your request for the preimage was not processed correctly, please try again." );
                    }
                }
                var json = {
                    "session_id": session_id,
                    "tx": tx
                };
                xhr.open( 'POST', 'https://app.lightningescrow.io/getpreimage/v2/' );
                xhr.setRequestHeader( 'Content-Type', 'application/json' );
                xhr.send( JSON.stringify( json ) );
```
