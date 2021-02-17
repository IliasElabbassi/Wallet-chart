from flask import Flask, render_template, request, make_response, redirect, url_for
import os
import json
from hashlib import sha256
from cryptography.fernet import Fernet 

app = Flask(__name__)

key = os.environ.get('KEY_CHART').encode('UTF-8')
fernet = Fernet(key)

@app.route('/')
def index():
    return render_template("front_page.html")

@app.route('/chart/add_crypto', methods=['GET', 'POST'])
def add_crypto():
    # if the cookie is not created create it
    if 'chart_data' not in request.cookies:
        return redirect(url_for('setcookie'))
    
    if request.method == 'POST':
        # we get the form
        new_datas = request.form
        
        # we load the cookie
        encrypted_cookie = request.cookies.get('chart_data') # string
        cookie = fernet.decrypt(encrypted_cookie.encode()).decode()
        json_data = json.loads(cookie) # json object 
        
        # if the form is empty we do not reformat the cookie, to insert the new value/values
        if new_datas["crypto_name0"] !=  ""  and new_datas["crypto_amount0"] != "":
            for amount in new_datas:
                if amount[0:13] == "crypto_amount":
                    try:
                        test = float(new_datas[amount])
                    except:
                        return render_template("error.html")
                
            # we format a new json string with the new values from the form and the values from the cookie
            data = format_data(json.dumps(new_datas), json.dumps(json_data))
            
            # we format the data in an array so it will be easier to print them in the template
            data_temp = json.loads(data)
            data_to_pass = []
            for value in data_temp["cryptos"]:
                data_to_pass.append((value["crypto_name"], value["crypto_amount"]))
            
            # we encrypt and update the cookie with the new values
            encrypt_cookie = fernet.encrypt(data.encode())            
            resp = make_response(render_template("add_crypto.html", datas=data_to_pass))
            resp.set_cookie('chart_data', encrypt_cookie)
            
            return resp  
        
        # we format the data in an array so it will be easier to print them in the template 
        data_to_pass = []
        for value in json_data["cryptos"]:
            data_to_pass.append((value["crypto_name"], value["crypto_amount"]))
        
        # render the template
        return render_template("add_crypto.html", datas=data_to_pass)
    else:
        # here we are in the get method, we only retrieve the cookie and print it
        encrypted_cookie = request.cookies.get('chart_data').encode()
        decrypted_cookie = fernet.decrypt(encrypted_cookie).decode()
        json_data = json.loads(decrypted_cookie)
        # we format the data in an array so it will be easier to print them in the template
        data_to_pass = []
        for value in json_data["cryptos"]:
            data_to_pass.append((value["crypto_name"], value["crypto_amount"]))
                
        return render_template("add_crypto.html", datas=data_to_pass)
    
@app.route('/getcookie')
def getcookie():
    encrypted_data = request.cookies.get('chart_data').encode()
    data = fernet.decrypt(encrypted_data).decode()
    
    return data

@app.route('/setcookie')
def setcookie():
    data = '{ "cryptos": [] }' # create the json string base
    encoded = fernet.encrypt(data.encode()) # we encrypt it
    resp = make_response(render_template("set_cookie.html"))
    resp.set_cookie('chart_data', encoded) # we set it
    
    return resp

@app.route('/chart')
def chart():
    # load cookie
    # load coinmarketcap price fro each crypto
    # create data crypto(amount) -> price ($) we may be able to choose later
    # create chart with data
    return "chart"
    
@app.route('/data/reset')
def resetData():
    data = '{ "cryptos": [] }'
    
    data_temp = json.loads(data)
    data_to_pass = []
    for value in data_temp["cryptos"]:
        data_to_pass.append((value["crypto_name"], value["crypto_amount"]))
        
    resp = make_response(render_template("add_crypto.html", datas=data_to_pass))
    resp.set_cookie('chart_data', data)
    
    return resp

@app.route('/test_format')
def test_format():
    
    new_data = {
        "crypto_name0": "luna",
        "crypto_amount0": "56",
        "crypto_name1": "BTC",
        "crypto_amount1": "456",
        "crypto_name2": "vet",
        "crypto_amount2": "1265",
        "crypto_name3": "ADA",
        "crypto_amount3": "68",
        "crypto_name4": "eth",
        "crypto_amount4": "0.25"
    }
    
    cookie_data = {
        "cryptos" : [
            {
                "crypto_name" : "LUNA",
                "crypto_amount" : "0.265",
                "price" : [
                    {
                        "date": "10/02/2020",
                        "price": "10"
                    },
                    {
                        "date": "11/02/2020",
                        "price": "12"
                    }
                ]
            },
            {
                "crypto_name" : "VET",
                "crypto_amount" : "45",
                "price" : [
                    {
                        "date": "10/02/2020",
                        "price": "15"
                    },
                    {
                        "date": "11/02/2020",
                        "price": "11"
                    }
                ]
            }
        ]
    }
    
    formated_data = format_data(json.dumps(new_data), json.dumps(cookie_data))
    
    #return render_template("test_format.html", cookie_data=cookie_data, new_data=new_data, formated=formated_data)
    return formated_data

def format_data(new_data, cookie_data):
    """
    new_data : 
    {
        crypto_name0: "luna",
        crypto_amount0: "0.265",
        crypto_name1: "btc",
        crypto_amount1: "1.365",
        ...
    }
    return (cookie_data+new_data well formated) : (if some tokens already are in cookie_data then we add their amount)
    {
        "cryptos" : [
            {
                "crypto_name" : "luna",
                "crypto_amount" : "0.265",
                "price" : [
                    {
                        "date": "10/02/2020",
                        "price": "10"
                    },
                    {
                        "date": "11/02/2020",
                        "price": "12"
                    }
                ]
            },
            {
                "crypto_name" : "vet",
                "crypto_amount" : "45",
                "price" : [
                    {
                        "date": "10/02/2020",
                        "price": "15"
                    },
                    {
                        "date": "11/02/2020",
                        "price": "11"
                    }
                ]
            }
        ]
    }
    """
    cookie_data = json.loads(cookie_data)
    new_data = json.loads(new_data)
    new_crypto = []
    new_amount = []
    formated_data = None
    temp = []
    
    for val in new_data:
        if val[0:11] == "crypto_name":
            new_crypto.append(new_data[val].upper())
        elif val[0:13] == "crypto_amount":
            new_amount.append(float(new_data[val]))

    if len(new_crypto) == len(new_amount):
        formated_data = []
        for i in range(0,len(new_crypto)):
            formated_data.append((new_crypto[i].upper(), float(new_amount[i])))

    crypto = []
    price = []
    
    for val in cookie_data["cryptos"]:
        crypto.append(val["crypto_name"].upper())
        price.append(float(val["crypto_amount"]))

    for i in range(0, len(new_crypto)):
        if new_crypto[i] in crypto:
            index = crypto.index(new_crypto[i])
            price[index] = price[index] + new_amount[i]
        else:
            crypto.append(new_crypto[i])
            price.append(new_amount[i])

    for c in cookie_data["cryptos"]:
        if c["crypto_name"] in crypto:
            index = crypto.index(c["crypto_name"])
            c["crypto_amount"] = price[index]
            
            crypto.remove(c["crypto_name"])
            price.remove(price[index])
    
    if len(crypto) != 0:
        for c in crypto:
            name = c
            amount = price[crypto.index(c)]
            data = {
                "crypto_name": name,
                "crypto_amount": amount,
                "price" : []
            }
            cookie_data["cryptos"].append(data)
        
    return  json.dumps(cookie_data, indent=2)


if __name__ == "__main__":
    app.run(debug=True, port=50)