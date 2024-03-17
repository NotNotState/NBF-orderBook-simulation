// Connect to SSE Server
//const active_table = $('#activetradescontainer').DataTable();
//import io from "../socket.io/socket.io.js"  

/**
add troublesome table for handling un initiated transactions
 */

$(document).ready(function() {
    let socket;
    let counter = 0;
    let tableDict = {};
    //Try global access, and try to set ordering = false
    table = new DataTable("#activeTradesTable", {
        //dom : 'Bfrtip',
        buttons: ['copyHtml5', 'csvHtml5', 'excelHtml5'],
        layout: {
            topStart: 'buttons'
        },
        deferRender : false,
        iDisplayLength : 100,
        //ordering : false
    });
    //Defaults sorting by time-stamp-epoch
    table.order([4, 'asc']).draw();

    function initializeSocket(){
        socket = io();
        socket.connect("http://127.0.0.1:5000/");
        socket.on("connect", function() {
            console.log("Client Connected")
            socket.emit("trans_processed");
    });

    socket.on("error_trans", function(){
        console.log("Triggered From Error");
        socket.emit("trans_processed");
    });

    socket.on("add_new_trans", function(data){
        // Check if ID is already in our tableDict with either id in tableDict OR tableDict.hasOwnProperty(id)
        //console.log(data);
        if (data.length > 0) {
            console.log("Triggered From Add New");
            add_table_row(data, counter);
            counter++;
        };

        socket.emit("trans_processed");
    });

    socket.on("update_trans", function(data){
        //Will likely need to add more here
        console.log("Triggered From Update");
        modify_row(data);
        socket.emit("trans_processed");
    });

    socket.on("log_complete_trans", function(data){
        console.log("Triggered From Complete");
        log_completed(data);
        socket.emit("trans_processed");
    });
    //caller function for log_completed()

    socket.on("Server Terminated", function(){
        //can add the display summary table function here

        console.log("Disconnecting Client")
        socket.disconnect();
    });

    };

    //Still need to test
    function modify_row(data){
        row_index = tableDict[data[1]][5];//pull the correct datatable row index
        //console.log(tableDict[data[1]]);
        temp = table.row(row_index).data();
        temp[1] = data[0];
        //table.row(row_index).data(temp).invalidate().draw(false);
        table.row(row_index).data(temp);
        table.draw();
    }

    function log_completed(data){
        //add if data[0] == "Cancelled" handling
        //row_index = tableDict[data[2]];//Is passing the enitre list!
        //console.log(tableDict[data[2]]);
        row_index = tableDict[data[2]][5];

        row = table.row(row_index).node();
        console.log(row);

        //Update background color
        if (data[0] == "Trade" && row != null){
            row.classList.add("lightGreen");    
        }else if(row != null){
            row.classList.add("lightRed");
        }else{
            console.log(table.row(row_index).data());
        }

        //Update State
        temp = table.row(row_index).data();
        temp[1] = data[0];
        //Remove Order ID from table
        table.row(row_index).data(temp);

        remove_from_tableDict(data[2]);

        table.draw();

    }

    function remove_from_tableDict(orderID){
        delete tableDict.orderID;
    }

    
    function add_table_row(data, row_number){
        // Append the received data as a new row to the DataTable
        //table.order(false).draw(false); // disable annoying auto sorting, MAY need to add back
        table.row.add([
            data[0], // Ticker
            data[1], // Status
            data[2], // Target Price
            data[3], // Exchange
            data[4]  // Request Time Epoch
        ]).draw(false); // false to prevent DataTable from redrawing the table

        //table.draw();

        tableDict[data[5]] = [
            data[0], // Ticker
            data[1], // Status
            data[2], // Target Price
            data[3], // Exchange
            data[4], //Request Time Epoch
            row_number, //Row number identifier
        ]

        table.draw();

    }

    initializeSocket();

})


