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

var alerts_db = new Map();
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

function format_db_message() {
  return {
    type: "alert_data",
    listen: status_listen,
    data: Array.from(alerts_db.values())
  };
}
function listenPopup(msg, portFrom) {
  if (msg.type == "POPUP_ALERTS") {
    console.log("Alert 1 received");
    portFrom.postMessage(format_db_message());
  } else if (msg.type == "POPUP_GROUPS")
    portFrom.postMessage({
      type: "alert_data",
      listen: status_listen,
      data: group()
    });
  else if (msg.type == "POPUP_CLEAN") {
    clean();
    portFrom.postMessage(format_db_message());
  } else if (msg.type == "POPUP_FLUSH") {
    flush();
    portFrom.postMessage(format_db_message());
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
    portFrom.postMessage({
      type: "alert_data",
      listen: status_listen,
      data: alerts_db
    });
  } else if (msg.type == "SEND_NATIVE") {
    sendNativeMessage(msg.value);
    console.log(portFrom);
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
        //console.log("Individual");
      }
      alert_full_data = message.payload.ret;
      if (alert_full_data.length < 1) return;
      //We add additional data to the message
      const completed_data = alert_full_data.map(add_info_message);

      //We check if the message is not already in the databases
      const new_data = completed_data.filter(msg => check_if_in_db(msg));
      // if there is no new message exit the function
      if (new_data.length < 1) return;
      //We add the new data to the database
      new_data.map(x => alerts_db.set(get_map_key(x), x));
      //TODO We send the message to the new database
      new_data.map(msg => sendNativeMessage(msg));

      //Put the messages as pending
      new_data.map(msg => (msg.status = "pending"));

      chrome.runtime.sendMessage(format_db_message(), function(response) {
        console.log(response);
      });
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
  //setTimeout(customAlerts, TIME_POLL);
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
function tdview_date_string_to_date(datestring) {
  const from = datestring.split(/ |:|\//);
  const nfrom_ = from.map(x => parseInt(x));
  return new Date(
    nfrom_[2],
    nfrom_[1] - 1,
    nfrom_[0],
    nfrom_[3],
    nfrom_[4],
    nfrom_[5]
  );
}
function add_info_message(msg) {
  if (!msg.grouped) {
    msg["number_message"] = 1;
    msg["time_last_fired"] = getTimeNow();
    msg["underlying"] = msg["underlying"].replace("Alert on", "");
  }
  msg["date_time_obj"] = tdview_date_string_to_date(msg["time_last_fired"]);
  msg["unix_fired_time"] = msg["date_time_obj"].getTime() / 1000;
  msg["status"] = "not treated";
  msg["id"] = get_map_key(msg);
  return msg;
}
//When we receive new message
function check_if_in_db(newData) {
  const check = get_map_key(newData);
  return !alerts_db.has(check);
}

function get_map_key(newData) {
  const { underlying, description, unix_fired_time } = newData;
  return Object.values({ underlying, description, unix_fired_time })
    .join()
    .replace(/ /g, "");
}

function clean() {
  for (var j = alerts_db.length - 1; j >= 0; j--) {
    if (alerts_db[j][4] != 0 && alerts_db[j][4] != 1)
      delete alerts_db.splice(j, 1);
  }
}

function flush() {
  alerts_db = new Map();
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
