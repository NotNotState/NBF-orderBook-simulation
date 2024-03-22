from flask import Flask, render_template
from flask_socketio import SocketIO
from helperFile import DateTimeFromUTC, read_transactions


#Global Variable Declaration
transactions = read_transactions("./appDir/dataDir/orderbook.json")
en_queue = {}
completed = {}

# composed of messages: CancelRequest, CancelAcknowledged, Cancelled, 
# and Trade BEFORE NewOrderRequest, or before we've seen a "NewOrderRequest" for that ID
troublesome = {} 

price_exposure = 0
n = 0 # global processor counter

#testing conditional flask rendering of results page
sim_complete = False

app = Flask(__name__)
#app.config["DEBUG"] = True
app.config['SECRETY_KEY'] = 'KIRI'
socket = SocketIO(app)

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
# Sets all global variables to init state, before process_transactions() is triggered to restart the simulation on page refresh
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
def process_transactions():
    """Function which creates simulation by iterating thorugh aggregate data and calling sse to update the webpage table(s)."""
    global n, price_exposure
    formatted_transaction = []
    if n < 7500:
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
                filled_time = DateTimeFromUTC(tranState["CompleteTimeEpoch"])
                formatted_transaction = [state, filled_price, filled_time, id]
                #formatted_transaction = [state, filled_price, id]
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
            socket.emit("error_trans")
        else:
            valueFormat["Ticker"] = tempTrans["Symbol"]
            valueFormat["Status"] = tempTrans["MessageType"]
            valueFormat["Exchange"] = tempTrans["Exchange"]
            valueFormat["TargetPrice"] = tempTrans["OrderPrice"]
            # Passes Time Objects as Human Friendly Format to Front End
            valueFormat["RequestTimeEpoch"] = DateTimeFromUTC(tempTrans["TimeStampEpoch"])
            
            valueFormat["Fill_time"] = valueFormat["Filled_price"] = "Pending..."

            en_queue[id] = valueFormat
            price_exposure += tempTrans["OrderPrice"]
            
            formatted_transaction = [valueFormat["Ticker"], valueFormat["Status"], valueFormat["TargetPrice"], valueFormat["Exchange"], 
                                     valueFormat["RequestTimeEpoch"], valueFormat["Fill_time"], valueFormat["Filled_price"], id]
            
            socket.emit("add_new_trans", formatted_transaction)
    else:
        #Trigger for Client to close connection
        socket.emit("Server Terminated")

    #increment global counter
    n+=1

if __name__ == "__main__":
    socket.run(app, allow_unsafe_werkzeug=True) 