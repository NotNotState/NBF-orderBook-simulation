from flask import Flask, render_template
from flask_socketio import SocketIO
import time
from app_old import read_transactions
import pandas as pd

#Global Variable Declaration
transactions = read_transactions("./appDir/dataDir/orderbook.json")
en_queue = {}
completed = {}
troublesome = {} # composed of messages: CancelRequest, CancelAcknowledged, Cancelled, and Trade BEFORE NewOrderRequest, or before we've seen a "NewOrderRequest" for that ID
price_exposure = 0
n = 0 # global processor counter

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRETY_KEY'] = 'KIRI'
socket = SocketIO(app,logger=True, engineio_logger=True)

#Flask Declarations
@app.route("/")
def main():
    return render_template("index.html")

@app.route('/results.html')
def results():
    return render_template('results.html')

@socket.on('connect')
def handle_connect():
    print("Client Connected")
    print("Counter at: ", n)

# Simulation Refresh Call
# Sets all global variables to init state, before process_transactions() is triggered
@socket.on("init_sim_seed")
def reset_n():
    global n, price_exposure, en_queue, completed, troublesome
    en_queue = {}
    completed = {}
    troublesome = {} 
    price_exposure = 0
    n = 0


#Main processor function
@socket.on("trans_processed")
def process_transactions() -> list:
    """Function which creates simulation by iterating thorugh aggregate data and calling sse to update the webpage table(s)."""
    global n, price_exposure
    #time.sleep(0.08)#time works perfectly here
    formatted_transaction = []
    if n < 1000:
        tempTrans = dict(transactions[n])
        id = tempTrans.pop("OrderID")
        valueFormat = {"Ticker": None, "Status": None, "TargetPrice": None, "Exchange": None}
        if id in en_queue:
            if tempTrans["MessageType"] == "Cancelled" or tempTrans["MessageType"] == "Trade": # () and tempTrans["Exchange"] == en_queue["Ticker"]["Exchange"] can handle with out if
                price_exposure -= en_queue[id]["TargetPrice"]
                tranState = en_queue[id]
                tranState["FilledPrice"] = tempTrans["OrderPrice"]
                tranState["CompleteTimeEpoch"] = tempTrans["TimeStampEpoch"]
                tranState["Status"] = tempTrans["MessageType"]

                # Start Socket message
                # 3 param packet for front end: Status Update for ticker (cancelled, traded), final price (if trade), and Ticker id
                completed[id] = tranState
                state = tempTrans["MessageType"]
                filled_price = tranState["FilledPrice"] if (tempTrans["OrderPrice"]) else "NA"
                formatted_transaction = [state, filled_price, id]
                socket.emit("log_complete_trans", formatted_transaction)
                # End Socket message

                # Remove cancelled or traded tickers from active trades dictionary
                en_queue.pop(id)
            else:
                en_queue[id]["Status"] = tempTrans["MessageType"]
                # Two param packet for front end: Status Update for ticker, and Ticker id
                formatted_transaction = [en_queue[id]["Status"], id]
                socket.emit("update_trans", formatted_transaction)
        
        elif tempTrans["MessageType"] != "NewOrderRequest":# Add some handling on Trade's for names not in the active book
            troublesome[id] = tempTrans
            socket.emit("error_trans")
        else:
            valueFormat["Ticker"] = tempTrans["Symbol"]
            valueFormat["Status"] = tempTrans["MessageType"]
            valueFormat["Exchange"] = tempTrans["Exchange"]
            valueFormat["TargetPrice"] = tempTrans["OrderPrice"]   
            valueFormat["RequestTimeEpoch"] = tempTrans["TimeStampEpoch"]
            en_queue[id] = valueFormat
            price_exposure += tempTrans["OrderPrice"]
            
            formatted_transaction = [valueFormat["Ticker"], valueFormat["Status"], valueFormat["TargetPrice"], valueFormat["Exchange"], valueFormat["RequestTimeEpoch"], id]
            socket.emit("add_new_trans", formatted_transaction)
    else:
        socket.emit("Server Terminated")
        print(len(troublesome))
        #call summary functions for final output
        return [pd.DataFrame.from_dict(completed, orient='index'), pd.DataFrame.from_dict(troublesome, orient='index'), pd.DataFrame.from_dict(en_queue, orient='index'), price_exposure]
    #increment global counter
    n+=1


if __name__ == "__main__":
    socket.run(app) 