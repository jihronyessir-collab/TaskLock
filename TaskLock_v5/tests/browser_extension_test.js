/** Logic-level Chromium MV3 background smoke test using a Chrome API stub. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const path=require('path');
const code=fs.readFileSync(path.join(__dirname,'../Browser_Extension/background.js'),'utf8');
let active=true,sites=['youtube.com','tiktok.com'],redirects=[];
const handlers={};
const chrome={
 action:{setBadgeText:async()=>{},setBadgeBackgroundColor:async()=>{}},
 alarms:{create:()=>{},onAlarm:{addListener:fn=>handlers.alarm=fn}},
 runtime:{onInstalled:{addListener:fn=>handlers.installed=fn},onStartup:{addListener:fn=>handlers.startup=fn},getURL:(s)=>'chrome-extension://test/'+s},
 webNavigation:{onBeforeNavigate:{addListener:fn=>handlers.navigate=fn}},
 tabs:{onUpdated:{addListener:fn=>handlers.updated=fn},query:async()=>[],update:async(id,args)=>{redirects.push([id,args.url])}}
};
const fetch=async()=>({ok:true,json:async()=>({active,sites})});
const ctx={chrome,fetch,URL,AbortSignal,Error,Array,console};
vm.runInNewContext(code,ctx,{filename:'background.js'});
(async()=>{
 await handlers.navigate({frameId:0,tabId:1,url:'https://m.youtube.com/watch?v=x'});
 assert.deepEqual(redirects,[[1,'chrome-extension://test/blocked.html']]);
 await handlers.navigate({frameId:0,tabId:2,url:'https://notyoutube.com/'});
 assert.equal(redirects.length,1);
 active=false;
 await handlers.navigate({frameId:0,tabId:3,url:'https://youtube.com/'});
 assert.equal(redirects.length,1);
 console.log('PASS extension blocks exact domains/subdomains, allows unrelated sites, respects pause');
})().catch(e=>{console.error(e);process.exit(1)});
