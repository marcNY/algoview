//document.getElementById('Button1').addEventListener('click', changeStatus("blue"));
//https://developer.chrome.com/extensions/messaging
var listen = true;

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

function display_one_message(msg) {
  const {
    underlying,
    description,
    number_message,
    time_last_fired,
    status
  } = msg;
  $("#message_table > tbody:last-child").append(
    `<tr><td>${underlying}</td><td>${status}</td><td>${description}</td><td>${number_message}</td><td>${
      time_last_fired.split(" ")[1]
    }</td></tr>`
  );
}
function displayArray(msg_array) {
  if (msg_array.length > 0) {
    //console.log("message of positive length received");
    clear_table();
    msg_array.map(msg => display_one_message(msg));
  }
}

$(function() {
  var port2 = chrome.extension.connect({ name: "popup" });

  var listen;
  port2.postMessage({ type: "POPUP_ALERTS" });

  port2.onMessage.addListener(function(msg) {
    console.log("message received:", msg);
    if (!msg.type || msg.type != "alert_data") return;
    if (!msg.data || msg.data.length < 1) return;
    displayArray(msg.data);
  });
  //MFN: THE FOLLOWING METHODS ARE LOADED WHEN THE PAGE IS LOADED

  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    console.log("message received:", request);
    if (!request.type || request.type != "alert_data") return;
    if (!request.data || request.data.length < 1) return;
    displayArray(request.data);
  });

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
    clear_table();
    port2.postMessage({ type: "POPUP_FLUSH" });
  });

  $("#ButtonDashboard").on("click", function() {
    chrome.tabs.create({ url: chrome.extension.getURL("dashboard.html") });
  });

  $("#ButtonSendNative").on("click", function() {
    let message = { type: "SEND_NATIVE", value: $("#message_to_host").val() };
    port2.postMessage(message);
    $("#message_to_host").val("");
    console.log("message sent:", message);
  });
});
