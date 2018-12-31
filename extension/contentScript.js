// Start connection in content script
let contentPort = chrome.runtime.connect({
  name: "tdview"
});

var id = -1;

// Listen for runtime message
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.action === "GET_ALARM") {
    var ret = [];
    id = message.id;
    try {
      x = document.getElementsByClassName(
        "js-alerts-multiple-notifications-dialog__table-container"
      );
      arr = Array.prototype.slice.call(x);
      console.log("arr:", arr);
      y = arr[0].children;
      arr2 = Array.prototype.slice.call(y);
      console.log("arr2:", arr2);
      z = arr2[0].children;
      arr3 = Array.prototype.slice.call(z); // [head, body]
      console.log("arr3:", arr3);
      a = arr3[1].children;
      arr4 = Array.prototype.slice.call(a); // [body]
      console.log("arr4:", arr4);
      for (var j = 0; j < arr4.length; j++) {
        z = arr4[j].children;
        arr5 = Array.prototype.slice.call(z); // [tds]
        console.log("arr5:", arr5);
        a = arr5[0].children; // div
        aa = Array.prototype.slice.call(a);
        aaa = aa[0].textContent;
        b = arr5[1].children; // div
        bb = Array.prototype.slice.call(b);
        bbb = bb[0].textContent;
        c = arr5[2].children; // div
        cc = Array.prototype.slice.call(c);
        ccc = cc[0].textContent;
        d = arr5[3].children; // div
        dd = Array.prototype.slice.call(d);
        ddd = dd[0].textContent;
        ret.push([aaa, bbb, ccc, ddd]);
      }
      if (arr4.length > 1) {
        console.log("Multiple alarms: ", ret);
      }
    } catch (err) {}
    contentPort.postMessage({
      //MFN: Posting Message
      type: "ALARM",
      payload: { id, ret }
    });
  }
});

// 0: div.tv-dialog.js-dialog.tv-dialog--popup.i-focused.ui-draggable
// "tv-dialog js-dialog tv-dialog--popup i-focused ui-draggable"
var statusAlert = document.body.contains(
  document.querySelector(".tv-alert-notification-dialog__head")
);

var observer = new MutationObserver(function(mutations) {
  nowAlert = document.body.contains(
    document.querySelector(".tv-alert-notification-dialog__head")
  );
  //console.log('*** ', [statusAlert, nowAlert, typeof statusAlert, typeof nowAlert]);
  if (statusAlert == false && nowAlert == true) {
    console.log("Single alert detected");
    x = document.getElementsByClassName("tv-alert-notification-dialog__head");
    arr = Array.prototype.slice.call(x);
    y = arr[0].children;
    arr2 = Array.prototype.slice.call(y);
    e = arr2[2];
    alert = arr2[1].textContent;
    desc = e.textContent;
    ret = [[alert, desc]];
    contentPort.postMessage({
      //MFN: sending message to the extension
      type: "INDIVIDUAL",
      payload: { id, ret }
    });
  }
  statusAlert = nowAlert;
});

observer.observe(document.body, { childList: true });
