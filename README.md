# NBF-orderBook-simulation
Simulating the message passing between National Bank and 3 separate exchanges over 3 minutes

### Methodology
After playing with the data, ideas for visualization became clear under an approach which (1) showed the speed at which these order/transactions were occuring and (2) tracked the state of the orders throughout the time period would be the best bet. Given the data followed a "Request" -> "Confirm" two way handshake built on order IDs, using dictionaries for tracking active, closed, and mis-matched orders made the most sense. Then simply iterating through an aggregate list of orders (sorted by Timestamp Epoch) and updating a log on the client side via websockets is very straighforward. I chose to do this with Datatables.js which allowed me to customize the appearance of the active trades on the client side. The websocket implementation was done using Flask's Websocket.io packages. 


### Data Observations and Simulation Assumptions
After performing some preliminary data analysis on the provided JSON files several observations became clear: 
1) Given the lack of "Buy", "Sell", or "Volume" tags any analysis on net exposure wouldn't be possible. Though I did include a summation of price exposure by Exchange. 
2) Only 20 trades were successfully executed through the entire process. These were trades which passed through the "NewOrderRequest" -> "NewOrderRequestAcknowledged" -> "Trade" sequence... Addtionally the request price matched the filled price exactly for these trades, which didn't allow for any analysis on price request/fill dynamics. 
3) The data begins at 9:28, but it became clear that the system had previously placed orders before the provided data began, so in some cirumstances an Exchange would send a "Trade" or "Cancel" confirmation for a ticker which had never been ordered (i.e. a "NewOrderRequest" for a given Order ID was never placed in the dataset. In that case I chose to log any "Cancels", "Trades", and "xxxConfirmed" messages from the Exchages on IDs which hadn't been logged as "mis-matched" messages. Since any analysis on Time-delta's or Price-delta's would be impossible given we don't know the original time-stamp of the request nor the requested price. 
