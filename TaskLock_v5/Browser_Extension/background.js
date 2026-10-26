const STATUS = 'http://127.0.0.1:18763/status';
let sites = [];
let active = false;
let connected = false;
async function refresh() {
  try {
    const response = await fetch(STATUS, {cache:'no-store', signal:AbortSignal.timeout(1800)});
    if (!response.ok) throw Error('TaskLock unavailable');
    const data = await response.json();
    sites = Array.isArray(data.sites) ? data.sites.filter(x => typeof x === 'string') : [];
    active = data.active === true;
    connected = true;
  } catch(e) {
    // Fail open: no site blocking if the desktop program isn't running.
    active = false; sites = []; connected = false;
  }
  await chrome.action.setBadgeText({text:!connected?'OFF':active?'ON':''});
  await chrome.action.setBadgeBackgroundColor({color:!connected?'#777777':'#a12525'});
}
function isBlocked(url) {
  if (!active) return false;
  try {
    const u = new URL(url);
    if (!['http:','https:'].includes(u.protocol)) return false;
    const host = u.hostname.toLowerCase().replace(/\.$/,'');
    return sites.some(s => host === s || host.endsWith('.'+s));
  } catch(e) {return false;}
}
async function check(tabId, url) {
  if (isBlocked(url)) {
    try {await chrome.tabs.update(tabId,{url:chrome.runtime.getURL('blocked.html')});} catch(e) {}
  }
}
chrome.runtime.onInstalled.addListener(async () => {
  chrome.alarms.create('refresh',{periodInMinutes:1});
  await refresh();
});
chrome.runtime.onStartup.addListener(async () => {
  chrome.alarms.create('refresh',{periodInMinutes:1});
  await refresh();
});
chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name !== 'refresh') return;
  await refresh();
  if (active) {
    const tabs = await chrome.tabs.query({});
    for (const tab of tabs) if (tab.id && tab.url) await check(tab.id,tab.url);
  }
});
chrome.webNavigation.onBeforeNavigate.addListener(async details => {
  if (details.frameId !== 0) return;
  await refresh();
  await check(details.tabId,details.url);
});
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.url) {await refresh(); await check(tabId,changeInfo.url);}
});
refresh();
