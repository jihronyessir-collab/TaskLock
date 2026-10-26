/* TaskLock: show verified public release assets with a GitHub Pages fallback. */
(async function () {
  const link = document.getElementById('download-link');
  const status = document.getElementById('download-status');
  const host = location.hostname.toLowerCase();
  let repo = '';
  if (host.endsWith('.github.io')) {
    const account = host.slice(0, -'.github.io'.length);
    const project = location.pathname.split('/').filter(Boolean)[0];
    if (account && project) repo = account + '/' + project;
  }
  if (!repo) {
    try {
      const response = await fetch('./release_config.json', {cache: 'no-store'});
      if (response.ok) {
        const config = await response.json();
        if (/^[\w.-]+\/[\w.-]+$/.test(config.github_repository || '')) {
          repo = config.github_repository;
        }
      }
    } catch (_) {}
  }
  if (!repo) {
    link.removeAttribute('href');
    link.textContent = 'Windows release unavailable';
    link.setAttribute('aria-disabled', 'true');
    status.textContent = 'The release repository is not configured.';
    return;
  }

  const findInstaller = files =>
    files.find(x => /^TaskLock-v[\d.]+-Setup\.exe$/i.test(x.name)) ||
    files.find(x => /^TaskLock-v[\d.]+-Windows\.zip$/i.test(x.name));

  async function getPublishedReleases() {
    const sources = [
      'https://api.github.com/repos/' + repo + '/releases?per_page=20',
      './release-info.json'
    ];
    for (const url of sources) {
      try {
        const response = await fetch(url, {cache: 'no-store', headers: {Accept: 'application/json'}});
        if (!response.ok) continue;
        const payload = await response.json();
        const releases = Array.isArray(payload) ? payload : payload.releases;
        if (Array.isArray(releases) && releases.length) return releases;
      } catch (_) {}
    }
    throw Error('Neither release source could be reached.');
  }

  try {
    const releases = await getPublishedReleases();
    const data = releases.find(x => !x.draft && findInstaller(x.assets || []));
    if (!data) throw Error('No Windows release available');
    const asset = findInstaller(data.assets || []);
    const expectedPrefix = 'https://github.com/' + repo + '/releases/download/' + data.tag_name + '/';
    if (!asset || !asset.browser_download_url.startsWith(expectedPrefix)) {
      throw Error('Invalid release asset URL');
    }
    link.href = asset.browser_download_url;
    link.removeAttribute('aria-disabled');
    link.textContent = 'Download TaskLock for Windows' + (data.prerelease ? ' (Beta)' : '');
    status.textContent = (data.prerelease ? 'Public beta ' : 'Published release ') +
      data.tag_name + ' · ' + (asset.size / 1048576).toFixed(1) + ' MB · Windows 10/11';
  } catch (_) {
    link.removeAttribute('href');
    link.textContent = 'Open GitHub Releases';
    link.href = 'https://github.com/' + repo + '/releases';
    link.removeAttribute('aria-disabled');
    status.textContent = 'Automatic release lookup is temporarily unavailable. You can still open GitHub Releases manually.';
  }
})();
