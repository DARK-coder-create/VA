let lifeline;

keepAlive();
console.log("Проверка");
startWebsocket();

chrome.runtime.onConnect.addListener(port => {
  if (port.name === 'keepAlive') {
    lifeline = port;
    setTimeout(keepAliveForced, 295e3); // 5 minutes minus 5 seconds
    port.onDisconnect.addListener(keepAliveForced);
  }
});

function keepAliveForced() {
  lifeline?.disconnect();
  lifeline = null;
  keepAlive();
}

async function keepAlive() {
  if (lifeline) return;
  for (const tab of await chrome.tabs.query({ url: '*://*/*' })) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: () => chrome.runtime.connect({ name: 'keepAlive' }),
        // `function` will become `func` in Chrome 93+
      });
      chrome.tabs.onUpdated.removeListener(retryOnTabUpdate);
      return;
    } catch (e) {}
  }
  chrome.tabs.onUpdated.addListener(retryOnTabUpdate);
}

async function retryOnTabUpdate(tabId, info, tab) {
  if (info.url && /^(file|https?):/.test(info.url)) {
    keepAlive();
  }
}


function startWebsocket(){
    ws = new WebSocket("ws://localhost:9090");

    ws.onmessage = function(mes) {
     console.log("onmessage");
     console.log(mes.data);

     try {
         var data = JSON.parse(mes.data)

         if (data.command == "open_tab") {
            console.log("open_tab" + data.url);

            if (data.url.length > 0) {
                chrome.tabs.create({ url: data.url });
            } else if (data.text.length > 0) {
                chrome.tabs.create({url: "https://www.google.com/search?q="+data.text})
         }}


         if (data.command == "switch_tab") {
            console.log("switch_tab " + data.number_tab);
            chrome.tabs.query({currentWindow: true}, function(tabs) {
            //chrome.tabs.update(tabs[data.number_tab - 1].id, {active: true});

             if (data.number_tab == 0) {
                chrome.tabs.update(tabs[tabs.length - 1].id, {active: true});
             } else {
                chrome.tabs.update(tabs[data.number_tab - 1].id, {active: true});
                }

            })
         }

         if (data.command == "remove_tab") {
            console.log("remove_tab " + data.number_tab);
            chrome.tabs.query({currentWindow: true}, function(tabs) {
            if (data.number_tab == 0) {
            chrome.tabs.remove(tabs[tabs.length - 1].id);
            } else {
                chrome.tabs.remove(tabs[data.number_tab - 1].id)
            }
            })
         }
         if (data.command == "close") {
            chrome.tabs.query({}, function (tabs) {
              for (var i = 0; i < tabs.length; i++) {
                  chrome.tabs.remove(tabs[i].id);
              }
            });
        }
     } catch (e) {
        console.log(e)
     }
     }
    ws.onopen = function() {
    console.log("open");
	//ws.send("test");
    };

    ws.onclose = function(){
        console.log("connection");
        // Try to reconnect in 5 seconds
        setTimeout(function(){startWebsocket()}, 3000);
    };
}