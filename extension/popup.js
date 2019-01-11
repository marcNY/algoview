//document.getElementById('Button1').addEventListener('click', changeStatus("blue"));
//https://developer.chrome.com/extensions/messaging

$(function() {
  var port2 = chrome.extension.connect({
    name: "popup"
  });

  var listen;
  port2.postMessage("POPUP_ALERTS");

  function updateButton() {
    if (listen) {
      $("#ButtonPause").html("Pause");
    } else {
      $("#ButtonPause").html("Resume");
    }
  }

  function clear_table() {
    $("#message_table tr:has(td)").remove();
  }
  port2.onMessage.addListener(function(msg) {
    //console.log("On page popup message has been received");
    listen = msg[1];
    updateButton();
    if (msg[0].length > 0) {
      //console.log("message of positive length received");
      clear_table();
      for (var j = 0; j < msg[0].length; j++) {
        let type = msg[0][j][6];
        let desc = msg[0][j][7];
        let iter = msg[0][j][2];
        let time = msg[0][j][3];
        let stat = msg[0][j][4];
        let status = "";
        if (stat == -3) {
          status = "Range";
        } else if (stat == -2) {
          status = "Malformed";
        } else if (stat < 0) {
          status = "Rejected";
        } else if (stat == 1) {
          status = "Part Filled";
        } else if (stat == 2) {
          status = "Filled";
        } else {
          if (j % 2 == 0) {
            status = "Grouped";
          } else {
            status = "pending";
          }
        }
        console.log(
          `<tr><td>${type}</td><td>${status}</td><td>${desc}</td><td>${iter}</td><td>${time}</td></tr>`
        );
        $("#message_table > tbody:last-child").append(
          `<tr><td>${type}</td><td>${status}</td><td>${desc}</td><td>${iter}</td><td>${time}</td></tr>`
        );
      }
    }
  });
  //MFN: THE FOLLOWING METHODS ARE LOADED WHEN THE PAGE IS LOADED

  $("#ButtonGroup").on("click", function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_GROUPS" });
  });
  $("#ButtonPause").on("click", function() {
    listen = !listen;
    updateButton();
    port2.postMessage({ type: "POPUP_EVENT" });
  });
  $("#ButtonClean").on("click", function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_CLEAN" });
  });
  $("#ButtonFlush").on("click", function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_FLUSH" });
  });

  $("#ButtonSendNative").on("click", function() {
    let message = { type: "SEND_NATIVE", value: $("#message_to_host").val() };
    port2.postMessage(message);
    $("#message_to_host").val("");
    console.log("message sent:", message);
  });
});
