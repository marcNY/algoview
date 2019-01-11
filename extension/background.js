// Platform

// Timing
const TIME_POLL = 1000;
const TIME_STATUS = 5000;
const T0 = parseInt((new Date("2018.12.09").getTime() / 1000).toFixed(0));
const ORANGE_POLL_MULTIPLIER = 5;
const URL = "tradingview.com/chart";
// Trading
const DEFAULT_K = 5000.0;
const DEFAULT_TF = 60;
const DEFAULT_X = 20;

// API

var lastrcv = 0;
var tab_ids = [];
var tab_n_polls = [];
var tab_n_recvs = [];
var thread_poll_id = 0;
var thread_status_id = 0;
var id_counter = (parseInt((Date.now() / 1000).toFixed(0)) - T0) * 100;

var alerts_db = [];
var orders_db = [];
var status_listen = true;

// On install ======================================================================================
chrome.runtime.onInstalled.addListener(function() {
  reset();
});

// On startup ======================================================================================
chrome.runtime.onStartup.addListener(function() {
  reset();
});

function listenPopup(msg, portFrom) {
  if (msg.type == "POPUP_ALERTS") {
    console.log("Alert 1 received");
    portFrom.postMessage([alerts_db, status_listen]);
  } else if (msg.type == "POPUP_GROUPS")
    portFrom.postMessage([group(), status_listen]);
  else if (msg.type == "POPUP_CLEAN") {
    clean();
    portFrom.postMessage([alerts_db, status_listen]);
  } else if (msg.type == "POPUP_FLUSH") {
    flush();
    portFrom.postMessage([alerts_db, status_listen]);
  } else if (msg.type == "POPUP_EVENT") {
    console.log("Alert 2 received");
    status_listen = !status_listen;
    if (status_listen == false) {
      clearInterval(thread_poll_id);
      chrome.browserAction.setBadgeBackgroundColor({ color: "RED" });
      console.log("Alerts suspended");
    } else {
      thread_poll_id = setInterval(poll, TIME_POLL);
      tabManager();
      console.log("Alerts resumed");
    }
    portFrom.postMessage([alerts_db, status_listen]);
  } else if (msg.type == "SEND_NATIVE") {
    sendNativeMessage(msg.value);
    console.log(portFrom);
    portFrom.postMessage([alerts_db, status_listen]);
  }
}
// New page / popup ================================================================================
chrome.runtime.onConnect.addListener(function(portFrom) {
  console.log("Listening from port: ", portFrom.name);
  if (portFrom.name === "tdview") {
    tabManager();
    portFrom.onMessage.addListener(function(message) {
      if (status_listen == false) {
        console.log("Warning: alerts suspended");
        return;
      }
      pushIndivdual = false;
      lastrcv = Date.now();
      if (message.type === "ALARM") {
        // Ordinary ping
        tab_n_recvs[message.payload.id] += 1;
      } else if (message.type === "INDIVIDUAL") {
        // Event from Contentscrpt
        pushIndivdual = true;
        console.log("Individual");
      }
      alert_full_data = message.payload.ret;

      // if (alert_full_data > 0) {
      //   console.log(alert_full_data);
      // }
      if (alert_full_data.length == 1 && alert_full_data[0].length == 2) {
        var temp = message.payload.ret[0][0].split(" ");
        alert_full_data = [
          [temp[temp.length - 1], message.payload.ret[0][1], 1, getTimeNow()]
        ];
      }
      for (var j = 0; j < alert_full_data.length; j++) {
        var newTwMessage = filter(alert_full_data[j], pushIndivdual);
        if (newTwMessage.length > 0) {
          console.log("New Message: ", newTwMessage);
          sendNativeMessage(newTwMessage);
        }
      }
    });
    if (thread_poll_id == 0) {
      thread_poll_id = setInterval(poll, TIME_POLL);
    }
  } else if (portFrom.name === "popup") {
    portFrom.onMessage.addListener(msg => listenPopup(msg, portFrom));
  }
});

// Tab closed ======================================================================================
chrome.tabs.onRemoved.addListener(function(tabId) {
  idx = tab_ids.indexOf(tabId);
  if (idx != -1) {
    delete tab_ids.splice(idx, 1);
    delete tab_n_polls.splice(idx, 1);
    delete tab_n_recvs.splice(idx, 1);
    console.log(
      "A Tradingview tab has been closed: " + tabId + ", Available: ",
      tab_ids.length
    );
  }
});

function getTimeNow() {
  var today = new Date();
  var date =
    ("0" + today.getDate()).slice(-2) +
    "/" +
    ("0" + (today.getMonth() + 1)).slice(-2) +
    "/" +
    today.getFullYear().toString();
  var time =
    ("0" + today.getHours()).slice(-2) +
    ":" +
    ("0" + today.getMinutes()).slice(-2) +
    ":" +
    ("0" + today.getSeconds()).slice(-2);
  var dateTime = date + " " + time;
  return dateTime;
}

function tabManager() {
  console.log("Tab Manager Called");
  tab_ids = [];
  tab_n_polls = [];
  tab_n_recvs = [];
  chrome.windows.getAll({ populate: true }, getRelevantTabs);
}

function poll() {
  for (var j = 0; j < tab_ids.length; j++) {
    chrome.tabs.sendMessage(tab_ids[j], { action: "GET_ALARM", id: j });
    tab_n_polls[j] += 1;
  }
}

function status() {
  //console.log("status_listen", status_listen);
  //console.log("tab ids length", tab_ids.length);
  if (status_listen == false) return;
  ok = 0;
  for (var j = 0; j < tab_ids.length && ok == 0; j++) {
    //console.log(j + " " + tab_n_polls[j] + " " + tab_n_recvs[j]);
    if (tab_n_polls[j] == tab_n_recvs[j]) ok = 1;
  }
  if (ok == 1) {
    chrome.browserAction.setBadgeBackgroundColor({ color: "GREEN" });
  } else if (Date.now() - lastrcv < TIME_POLL * ORANGE_POLL_MULTIPLIER) {
    chrome.browserAction.setBadgeBackgroundColor({ color: "ORANGE" });
  } else {
    chrome.browserAction.setBadgeBackgroundColor({ color: "RED" });
  }
}

function setCharAt(str, index, chr) {
  if (index > str.length - 1) return str;
  return str.substr(0, index) + chr + str.substr(index + 1);
}

function positiveTime(strA, strB) {
  a_ = strA;
  b_ = strB;
  a_ = setCharAt(a_, 0, strA[3]);
  a_ = setCharAt(a_, 1, strA[4]);
  a_ = setCharAt(a_, 3, strA[0]);
  a_ = setCharAt(a_, 4, strA[1]);
  b_ = setCharAt(b_, 0, strB[3]);
  b_ = setCharAt(b_, 1, strB[4]);
  b_ = setCharAt(b_, 3, strB[0]);
  b_ = setCharAt(b_, 4, strB[1]);
  t1 = Date.parse(a_);
  t2 = Date.parse(b_);

  return t2 - t1;
}

function reset() {
  setTimeout(customAlerts, TIME_POLL);
  //customAlerts();
  chrome.browserAction.setBadgeText({ text: " " });
  chrome.browserAction.setBadgeBackgroundColor({ color: "RED" });
  if (thread_poll_id != 0) clearInterval(thread_poll_id);
  if (thread_status_id != 0) clearInterval(thread_status_id);
  setInterval(status, TIME_STATUS);
}

function getRelevantTabs(winData) {
  console.log("Calling getRelevantTabs");
  for (var i in winData) {
    var winTabs = winData[i].tabs;
    var totTabs = winTabs.length;
    for (var j = 0; j < totTabs; j++) {
      //console.log(winTabs[j].url);
      if (
        typeof winTabs[j].url !== "undefined" &&
        winTabs[j].url.includes(URL)
      ) {
        tab_ids.push(winTabs[j].id);
        tab_n_polls.push(0);
        tab_n_recvs.push(0);
      }
    }
  }
}

function filter(newData, individual) {
  var ok = 1;
  newData[2] = parseInt(newData[2]);
  var type = newData[0];
  var desc = newData[1];
  var iter = newData[2];
  var time = newData[3];

  for (var j = 0; j < alerts_db.length && ok == 1; j++) {
    //console.log('filtering ' + newData + ' '+ time + ' '+alerts_db[j][3]+ ' '+(time - alerts_db[j][3]));
    if (individual) {
      if (type != alerts_db[j][0]) continue;
      if (desc != alerts_db[j][1]) continue;
      if (positiveTime(alerts_db[j][3], time) > 0) continue;
      ok = 0;
    } else {
      if (type != alerts_db[j][0]) continue;
      if (desc != alerts_db[j][1]) continue;
      if (iter > alerts_db[j][2]) continue;
      if (iter > 1) {
        if (positiveTime(alerts_db[j][3], time) > 0) continue;
      }
      ok = 0;
    }
  }
  if (ok == 1) {
    db_add(newData);
    return newData;
  } else {
    return [];
  }
}

function db_add(newData) {
  ret = prepare(newData);
  accepted = ret[0];
  params = ret[1];
  desc = ret[2];
  title = params[0];
  init_status = 0;

  if (!accepted) {
    newData.push(-2);
    newData.push(-1);
  } else {
    newData.push(0);
    newData.push(id_counter);
    //orderAdd(params, id_counter);
    id_counter++;
  }
  newData.push(title);
  newData.push(desc);
  alerts_db.push(newData);
  //console.log('Alert added: ' + newData);
  //console.log(alerts_db);
}

function clean() {
  for (var j = alerts_db.length - 1; j >= 0; j--) {
    if (alerts_db[j][4] != 0 && alerts_db[j][4] != 1)
      delete alerts_db.splice(j, 1);
  }
}

function flush() {
  delete alerts_db.splice(0);
}

function group() {
  g = [];

  for (var j = 0; j < alerts_db.length; j++) {
    type = alerts_db[j][0];
    desc = alerts_db[j][1];
    iter = alerts_db[j][2];
    time = alerts_db[j][3];
    title = alerts_db[j][6];
    desc2 = alerts_db[j][7];
    found = 0;
    for (var k = 0; k < g.length && found == 0; k++) {
      if (type == g[k][0] && desc == g[k][1]) {
        g[k][2] = g[k][2] + iter;
        g[k][3] = time;
        found = 1;
      }
    }
    if (found == 0) {
      g.push([type, desc, iter, time, 99, 0, title, desc2]);
    }
  }

  return g;
}

function customAlerts() {}

function prepare(msg) {
  title = -1;
  direction = -1;
  price = -1;
  quantity = -1;
  type = -1;
  exchange = -1;
  symbol = -1;
  x = DEFAULT_X;
  tf = DEFAULT_TF;
  m = false;
  accepted = true;

  params = msg[1].split(" ");

  for (var k = 0; k < params.length && accepted; k++) {
    lr = params[k].split("=");
    if (lr.length != 2) accepted = false;
    if (lr[0] == "d") {
      if (lr[1] == "long" || lr[1] == "short") {
        direction = lr[1];
      }
    } else if (lr[0] == "m") {
      if (lr[1] == "true") m = true;
      else if (lr[1] == "false") m = false;
      else m = -1;
    } else if (lr[0] == "tf") {
      z = parseFloat(lr[1]);
      if (!isNaN(z) && z > 0.0) {
        tf = z;
      } else accepted = false;
    } else if (lr[0] == "x") {
      x = parseFloat(lr[1]);
      if (!isNaN(z) && x > 0.0) {
      } else accepted = false;
    } else if (lr[0] == "n") {
      title = lr[1];
    } else if (lr[0] == "p") {
      z = parseFloat(lr[1]);
      if (!isNaN(z)) {
        price = z;
      }
    } else if (lr[0] == "q") {
      z = parseFloat(lr[1]);
      if (!isNaN(z)) {
        quantity = z;
      }
    } else if (lr[0] == "t") {
      if (lr[1] == "l" || lr[1] == "m") {
        type = lr[1];
      }
    } else if (lr[0] == "e") {
      if (EXCHANGES.indexOf(lr[1]) < 0) return [];
      exchange = lr[1];
    } else if (lr[0] == "s") {
      symbol = lr[1];
    } else {
      console.log("ERROR: symbol ", lr[0]);
      accepted = false;
    }
  }

  if (
    m == -1 ||
    title == -1 ||
    direction == -1 ||
    price == -1 ||
    quantity == -1 ||
    type == -1 ||
    exchange == -1 ||
    symbol == -1
  ) {
    accepted = false;
    fullDesc = msg[1];
  } else if (
    m == true &&
    ((direction == "long" && price > 0) || (direction == "short" && price < 0))
  ) {
    console.log("Rejected (m == true)");
    accepted = false;
    fullDesc = msg[1];
  } else {
    // Compulsory params
    fullDesc =
      "d=" +
      direction +
      " t=" +
      type +
      " p=" +
      price +
      " q=" +
      quantity +
      " s=" +
      symbol +
      " e=" +
      exchange;
    // Optional params
    if (m != false) fullDesc = fullDesc + " m=" + m;
    if (x != DEFAULT_X) fullDesc = fullDesc + " x=" + x;
    if (tf != DEFAULT_TF) fullDesc = fullDesc + " tf=" + tf;
  }

  return [
    accepted,
    [title, direction, price, quantity, type, exchange, symbol, m, x, tf],
    fullDesc
  ];
}

function updateAlert(id, status) {
  console.log("updating alerts");
  for (var j = 0; j < alerts_db.length; j++) {
    if (alerts_db[j][5] == id) {
      alerts_db[j][4] = status;
      return;
    }
  }
}
