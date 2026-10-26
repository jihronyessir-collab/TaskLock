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
    const response = await fetch('https://api.github.com/repos/'+repo+'/releases?per_page=15',
      {headers:{Accept:'application/vnd.github+json'}});
    if (!response.ok) throw Error('No release published');
    const releases = await response.json();
    if (!Array.isArray(releases)) throw Error('Invalid release data');
    const findInstaller = files => files.find(x=>/^TaskLock-v[\d.]+-Setup\.exe$/i.test(x.name)) ||
      files.find(x=>/^TaskLock-v[\d.]+-Windows\.zip$/i.test(x.name));
    const data = releases.find(x=>!x.draft && findInstaller(x.assets || []));
    if (!data) throw Error('No Windows release available');
    const asset = findInstaller(data.assets || []);
    if (!asset || !asset.browser_download_url.startsWith('https://github.com/')) throw Error('No Windows release asset');
    link.href=asset.browser_download_url;
    link.removeAttribute('aria-disabled');
    link.textContent = 'Download TaskLock for Windows'+(data.prerelease?' (Beta)':'');
    status.textContent = (data.prerelease?'Public beta':'Published release')+' '+data.tag_name+' · '+(asset.size/1048576).toFixed(1)+' MB · Windows 10/11';
  } catch (err) {
    link.removeAttribute('href');
    link.textContent='Windows release coming soon';
    link.setAttribute('aria-disabled','true');
    status.textContent='The source is available, but the Windows installer has not been publicly released.';
  }
})();
