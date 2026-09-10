/* ==================================================================
   feed proxy — a cloudflare worker for player. (and later youtube)

   why: podcast RSS feeds rarely send CORS headers, so the r1 webview
   can't fetch them directly. this worker fetches the feed and returns
   it with the headers the webview needs. audio itself streams straight
   from the podcast's CDN — only the feed XML comes through here.

   setup (once, ~5 minutes, free):
   1. dash.cloudflare.com → sign up / sign in
   2. Workers & Pages → Create → Create Worker → deploy the hello-world
   3. Edit code → replace everything with this file → Deploy
   4. your worker lives at https://NAME.YOUR-SUBDOMAIN.workers.dev
      → paste that (with /?url= on the end) into PROXY in index.html

   IMPORTANT — edit ALLOW_HOSTS below to the hostnames of your feeds,
   otherwise this is an open proxy anyone can abuse.
================================================================== */

const ALLOW_HOSTS = [
  'feeds.simplecast.com', 'feeds.acast.com',           // ← replace with your feed hosts, e.g.
  // 'feeds.simplecast.com',
  // 'feeds.megaphone.fm',
  // 'anchor.fm',
];

export default {
  async fetch(request) {
    const u = new URL(request.url).searchParams.get('url');
    if (!u) return cors(new Response('missing ?url=', { status: 400 }));

    let target;
    try { target = new URL(u); } catch (e) {
      return cors(new Response('bad url', { status: 400 }));
    }
    const allowed = ALLOW_HOSTS.some(h =>
      target.hostname === h || target.hostname.endsWith('.' + h));
    if (!allowed) return cors(new Response('host not in allowlist', { status: 403 }));

    // cache feeds for 10 minutes so repeated opens are instant
    const upstream = await fetch(target.toString(), {
      cf: { cacheTtl: 600, cacheEverything: true },
      headers: { 'User-Agent': 'player-r1-feed-proxy' },
    });

    const body = await upstream.arrayBuffer();
    const resp = new Response(body, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('Content-Type') || 'application/xml',
        'Cache-Control': 'public, max-age=600',
      },
    });
    return cors(resp);
  },
};

function cors(resp) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
  return resp;
}
