/* TaskLock v5: only show verified published release assets; no fictitious URLs. */
(async function () {
  const link = document.getElementById('download-link');
  const status = document.getElementById('download-status');
  const host = location.hostname.toLowerCase();
  let repo = '';
  if (host.endsWith('.github.io')) {
    const account = host.slice(0,-'.github.io'.length);
    const project = location.pathname.split('/').filter(Boolean)[0];
    if (account && project) repo = account + '/' + project;
  }
  if (!repo) {
    try {
      const response = await fetch('./release_config.json', {cache:'no-store'});
      if (response.ok) {
        const config = await response.json();
        if (/^[\w.-]+\/[\w.-]+$/.test(config.github_repository || '')) repo=config.github_repository;
      }
    } catch (_) {}
  }
  if (!repo) {
    link.removeAttribute('href');
    link.textContent = 'Windows release coming soon';
    link.setAttribute('aria-disabled','true');
    status.textContent = 'The website is ready, but no public Windows installer has been published yet.';
    return;
  }
  try {
    const response = await fetch('https://api.github.com/repos/'+repo+'/releases/latest',
      {headers:{Accept:'application/vnd.github+json'}});
    if (!response.ok) throw Error('No release published');
    const data = await response.json();
    const files = data.assets || [];
    const asset = files.find(x=>/^TaskLock-v[\d.]+-Setup\.exe$/i.test(x.name)) ||
                  files.find(x=>/^TaskLock-v[\d.]+-Windows\.zip$/i.test(x.name));
    if (!asset || !asset.browser_download_url.startsWith('https://github.com/')) throw Error('No Windows release asset');
    link.href=asset.browser_download_url;
    link.removeAttribute('aria-disabled');
    link.textContent = 'Download '+asset.name;
    status.textContent = 'Published '+data.tag_name+' · '+(asset.size/1048576).toFixed(1)+' MB';
  } catch (err) {
    link.removeAttribute('href');
    link.textContent='Windows release coming soon';
    link.setAttribute('aria-disabled','true');
    status.textContent='The source is available, but the Windows installer has not been publicly released.';
  }
})();
