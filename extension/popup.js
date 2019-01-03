function changeStatus(vcolor) {}

//document.getElementById('Button1').addEventListener('click', changeStatus("blue"));
//https://developer.chrome.com/extensions/messaging
var port2 = chrome.extension.connect({
  name: "popup"
});

const PARTFILLED =
  "width: 80px; max-width:80px; background-color: #fafafa; color:orange; font-weight: bold";
const PARTFILLED2 =
  "width: 80px; max-width:80px; background-color: #eeeeee; color:orange; font-weight: bold";
const FILLED =
  "width: 80px; max-width:80px; background-color: #fafafa; color:green; font-weight: bold";
const FILLED2 =
  "width: 80px; max-width:80px; background-color: #eeeeee; color:green; font-weight: bold";
const PENDING = "width: 80px; max-width:80px; background-color: #fafafa;";
const PENDING2 = "width: 80px; max-width:80px; background-color: #eeeeee;";
const REJECTED =
  "width: 80px; max-width:80px; background-color: #fafafa; color:red; font-weight: bold";
const REJECTED2 =
  "width: 80px; max-width:80px; background-color: #eeeeee; color:red; font-weight: bold";

var listen;
port2.postMessage("POPUP_ALERTS");

function updateButton() {
  if (listen) {
    $("#ButtonPoll").html("Pause");
  } else {
    $("#ButtonPoll").html("Resume");
  }
}
port2.onMessage.addListener(function(msg) {
  console.log("Message received :) :)", msg);
});

port2.onMessage.addListener(function(msg) {
  x = document.getElementById("popup_text");
  listen = msg[1];
  updateButton();
  if (msg[0].length > 0) {
    x.innerHTML = "";
    z = document.createElement("div");
    z.setAttribute("id", "dynamicModule");
    //<div id= "dynamicModule"></div>
    y = document.createElement("div");
    a = document.createElement("div");
    a.setAttribute(
      "style",
      "width: 90px; max-width:90px; font-style: italic; font-weight: bold; background-color: #dddddd;"
    );
    aa = document.createTextNode("Title");
    e = document.createElement("div");
    e.setAttribute(
      "style",
      "width: 80px; max-width:80px; font-style: italic; font-weight: bold; background-color: #dddddd;"
    );
    ee = document.createTextNode("Status");
    b = document.createElement("div");
    b.setAttribute(
      "style",
      "width: 360px; max-width:360px; font-style: italic; font-weight: bold; background-color: #dddddd;"
    );
    bb = document.createTextNode("Description");
    c = document.createElement("div");
    c.setAttribute(
      "style",
      "width: 38px; max-width:38px; text-align:left; font-style: italic; font-weight: bold; background-color: #dddddd;"
    );
    cc = document.createTextNode("#");
    d = document.createElement("div");
    d.setAttribute(
      "style",
      "13px; width: 120px; max-width:120px; text-align:left; font-style: italic; font-weight: bold; background-color: #dddddd;"
    );
    dd = document.createTextNode("Timestamp");

    a.appendChild(aa);
    b.appendChild(bb);
    c.appendChild(cc);
    d.appendChild(dd);
    e.appendChild(ee);
    y.appendChild(a);
    y.appendChild(e);
    y.appendChild(b);
    y.appendChild(c);
    y.appendChild(d);
    y.setAttribute("style", "display:inline-flex");
    z.appendChild(y);

    document.body.insertBefore(z, x);
  }
  for (var j = 0; j < msg[0].length; j++) {
    type = msg[0][j][6];
    desc = msg[0][j][7];
    iter = msg[0][j][2];
    time = msg[0][j][3];
    stat = msg[0][j][4];

    y = document.createElement("div");
    a = document.createElement("div");
    if (j % 2 == 0)
      a.setAttribute(
        "style",
        "width: 90px; max-width:110px; font-weight: bold; background-color: #fafafa;"
      );
    else
      a.setAttribute(
        "style",
        "width: 90px; max-width:110px; font-weight: bold; background-color: #eeeeee;"
      );
    aa = document.createTextNode(type);
    e = document.createElement("div");
    if (stat < 0) {
      if (j % 2 == 0) e.setAttribute("style", REJECTED);
      else e.setAttribute("style", REJECTED2);
      if (stat == -3) ee = document.createTextNode("Range");
      else if (stat == -2) ee = document.createTextNode("Malformed");
      else ee = document.createTextNode("Rejected");
    } else if (stat == 1) {
      if (j % 2 == 0) e.setAttribute("style", PARTFILLED);
      else e.setAttribute("style", PARTFILLED2);
      ee = document.createTextNode("Part filled");
    } else if (stat == 2) {
      if (j % 2 == 0) e.setAttribute("style", FILLED);
      else e.setAttribute("style", FILLED2);
      ee = document.createTextNode("Filled");
    } else {
      if (j % 2 == 0) e.setAttribute("style", PENDING);
      else e.setAttribute("style", PENDING2);
      ee = document.createTextNode("Grouped");
      if (stat == 99) ee = document.createTextNode("Grouped");
      else ee = document.createTextNode("Pending");
    }

    b = document.createElement("div");
    if (j % 2 == 0)
      b.setAttribute(
        "style",
        "width: 360px; max-width:360px; background-color: #fafafa;"
      );
    else
      b.setAttribute(
        "style",
        "width: 360px; max-width:360px; background-color: #eeeeee;"
      );
    bb = document.createTextNode(desc);
    c = document.createElement("div");
    if (j % 2 == 0)
      c.setAttribute(
        "style",
        "width: 38px; max-width:38px; text-align:left; background-color: #fafafa;"
      );
    else
      c.setAttribute(
        "style",
        "width: 38px; max-width:38px; text-align:left; background-color: #eeeeee;"
      );
    cc = document.createTextNode(iter);
    d = document.createElement("div");
    if (j % 2 == 0)
      d.setAttribute(
        "style",
        "width: 120px; max-width:120px; text-align:left; background-color: #fafafa;"
      );
    else
      d.setAttribute(
        "style",
        "width: 120px; max-width:120px; text-align:left; background-color: #eeeeee;"
      );
    dd = document.createTextNode(time);

    a.appendChild(aa);
    b.appendChild(bb);
    c.appendChild(cc);
    d.appendChild(dd);
    e.appendChild(ee);
    y.appendChild(a);
    y.appendChild(e);
    y.appendChild(b);
    y.appendChild(c);
    y.appendChild(d);
    y.setAttribute("style", "display:inline-flex");

    z.appendChild(y);
  }
  if (msg[0].length > 0) {
    document.body.insertBefore(z, x);
  }
});
//MFN: THE FOLLOWING METHODS ARE LOADED WHEN THE PAGE IS LOADED
$(function() {
  $("#ButtonGroup").click(function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_GROUPS" });
  });
  $("#ButtonPoll").click(function() {
    listen = !listen;
    updateButton();
    port2.postMessage({ type: "POPUP_EVENT" });
  });
  $("#ButtonClean").click(function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_CLEAN" });
  });
  $("#ButtonFlush").click(function() {
    x = $("#dynamicModule");
    if (x != null) x.remove();
    port2.postMessage({ type: "POPUP_FLUSH" });
  });

  $("#ButtonSendNative").click(function() {
    let message = { type: "SEND_NATIVE", value: $("#message_to_host").val() };
    port2.postMessage(message);
    console.log("message sent:", message);
  });
});
