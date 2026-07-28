/**
 * opencli adapter: coursera download
 * Part of mooc2handout-skill multi-platform pipeline.
 *
 * Strategy : DOM_STATE (browser: true, COOKIE auth)
 * Contract : visible-ui — locale-independent attribute selectors throughout.
 *
 * URL modes (auto-detected):
 *   Course home  → https://www.coursera.org/learn/COURSE
 *   Welcome page → https://www.coursera.org/learn/COURSE/home/welcome
 *   Single module→ https://www.coursera.org/learn/COURSE/home/module/N
 *
 * Usage:
 *   opencli coursera download "https://www.coursera.org/learn/COURSE"            # all modules
 *   opencli coursera download "https://www.coursera.org/learn/COURSE/home/module/2"  # one module
 *   opencli coursera download "URL" --out ./notes --langs "en,zh-CN,zh-TW" --locale en
 *   opencli coursera download "URL" --langs "en"
 *   opencli coursera download "URL" --langs all
 *   opencli coursera download "URL" --video
 */

import { cli, Strategy } from '@jackwener/opencli/registry';
import fs    from 'fs';
import path  from 'path';
import https from 'https';
import http  from 'http';
import { spawnSync } from 'child_process';

// ─── helpers ──────────────────────────────────────────────────────────────────

/** Download a pre-signed URL to disk, follows HTTP redirects */
function downloadUrl(url, dest) {
  return new Promise((resolve, reject) => {
    const go = (u, hops = 0) => {
      if (hops > 10) return reject(new Error('too many redirects'));
      const mod = u.startsWith('https') ? https : http;
      mod.get(u, (res) => {
        if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location) {
          res.resume(); go(res.headers.location, hops + 1); return;
        }
        if (res.statusCode !== 200) {
          res.resume(); return reject(new Error(`HTTP ${res.statusCode}`));
        }
        const file = fs.createWriteStream(dest);
        res.pipe(file);
        file.on('finish', () => { file.close(); resolve(fs.statSync(dest).size); });
        res.on('error', reject); file.on('error', reject);
      }).on('error', reject);
    };
    go(url);
  });
}

/** Convert a lecture title to a safe filename slug */
function toSlug(text) {
  return text
    .replace(/[^\w\u4e00-\u9fff\s-]/g, '')
    .replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
    .toLowerCase().slice(0, 60) || 'lecture';
}

function humanSize(b) {
  if (b < 1024)         return `${b}B`;
  if (b < 1024 * 1024)  return `${(b / 1024).toFixed(1)}K`;
  return `${(b / 1024 / 1024).toFixed(1)}M`;
}

/** Append ?hl=<locale> to a URL to force Coursera UI language */
function withLocale(url, locale) {
  if (!locale) return url;
  const u = new URL(url); u.searchParams.set('hl', locale); return u.toString();
}

/**
 * Detect whether the given URL is a single-module URL or a course-level URL.
 * Returns: { type: 'module', moduleNum: N } | { type: 'course' }
 */
function detectUrlType(url) {
  const m = url.match(/\/home\/module\/(\d+)/);
  if (m) return { type: 'module', moduleNum: parseInt(m[1], 10) };
  return { type: 'course' };
}

/**
 * Navigate to a course welcome/home page and collect all module URLs.
 * Works regardless of UI locale (uses href pattern matching).
 */
async function discoverModules(page, courseUrl, locale, delay) {
  // Normalize to /home/welcome (works from any course sub-page)
  const base = courseUrl.replace(/\/(home\/.*)$/, '');
  const welcomeUrl = withLocale(`${base}/home/welcome`, locale);

  console.error(`[coursera-dl] Navigating to welcome page: ${welcomeUrl}`);
  await page.goto(welcomeUrl);
  await new Promise((r) => setTimeout(r, delay));

  const modules = await page.evaluate(() => {
    // <a href=".../.../home/module/N"> — locale-independent
    const seen = new Set();
    return Array.from(document.querySelectorAll('a[href*="/home/module/"]'))
      .map((a) => {
        const href = a.href.split('?')[0]; // strip query params
        const m = href.match(/\/home\/module\/(\d+)$/);
        if (!m || seen.has(href)) return null;
        seen.add(href);

        // Try to get a human-readable module name from the link text
        const raw = a.textContent.trim().replace(/\s+/g, ' ');
        return { num: parseInt(m[1], 10), href, text: raw || `Module ${m[1]}` };
      })
      .filter(Boolean)
      .sort((a, b) => a.num - b.num);
  });

  return modules;
}

// ─── per-module subtitle + video download ─────────────────────────────────────

async function downloadModule(page, { moduleUrl, outDir, langList, downloadAll, locale, video, resources, delay, results }) {
  const localeUrl = withLocale(moduleUrl, locale);
  console.error(`[coursera-dl] Module: ${localeUrl}`);

  await page.goto(localeUrl);
  await new Promise((r) => setTimeout(r, delay));

  // Collect lecture links — detect locked items via aria-label (locale-specific text
  // but always appended as ", 锁定" in zh-CN UI or ", locked" in en UI) and SVG lock icon.
  const lectures = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href*="/lecture/"]')).map((a) => {
      const nameEl    = a.querySelector('[data-test="rc-ItemName"]');
      const raw       = (nameEl || a).textContent.trim().replace(/\s+/g, ' ');
      const clean     = raw.replace(/\s*(视频|Video)[^•]*•.*/i, '').trim();
      const ariaLabel = a.getAttribute('aria-label') || '';
      const hasLockIcon = !!a.querySelector('[data-testid*="lock"], [class*="lock"]');
      // Coursera appends ", 锁定" (zh) or ", locked" (en) to aria-label for locked items
      const locked = hasLockIcon || /,\s*(锁定|locked)/i.test(ariaLabel);
      return { text: clean || raw, href: a.href, locked };
    })
  );

  fs.mkdirSync(outDir, { recursive: true });

  for (let i = 0; i < lectures.length; i++) {
    const { text, href, locked } = lectures[i];
    const slug   = `${String(i + 1).padStart(2, '0')}_${toSlug(text)}`;
    const rowNum = i + 1;

    // Skip locked lectures — subtitles are inaccessible without full enrollment
    if (locked) {
      results.push({ lecture: text.slice(0, 35), type: 'sub', lang: '—', file: '—', status: '🔒 locked (skipped)' });
      continue;
    }

    const lectureUrl = withLocale(href, locale);
    await page.goto(lectureUrl);
    await new Promise((r) => setTimeout(r, delay));

    // Wait for <track> elements (up to 10 s extra)
    for (let t = 0; t < 5; t++) {
      const found = await page.evaluate(() => document.querySelectorAll('track[kind="captions"]').length > 0);
      if (found) break;
      await new Promise((r) => setTimeout(r, 2000));
    }

    // ── Subtitles ────────────────────────────────────────────────────────────
    const tracks = await page.evaluate(() =>
      Array.from(document.querySelectorAll('track[kind="captions"]')).map((t) => ({
        lang: t.srclang, src: t.src, label: t.label,
      }))
    );

    const targets = downloadAll
      ? [...new Set(tracks.map((t) => t.lang))]
      : langList;

    for (const lang of targets) {
      const track = tracks.find((t) => t.lang === lang);
      if (!track) {
        if (!downloadAll)
          results.push({ lecture: text.slice(0, 35), type: 'sub', lang, file: '—', status: '⚠ n/a' });
        continue;
      }
      const filename = `${slug}.${lang}.vtt`;
      const filepath = path.join(outDir, filename);
      try {
        const bytes = await downloadUrl(track.src, filepath);
        results.push({ lecture: text.slice(0, 35), type: 'sub', lang, file: filename, status: `✓ ${humanSize(bytes)}` });
      } catch (e) {
        results.push({ lecture: text.slice(0, 35), type: 'sub', lang, file: filename, status: `✗ ${String(e.message).slice(0, 40)}` });
      }
    }

    // ── Video (optional) ─────────────────────────────────────────────────────
    if (!video) continue;

    const videoFilename = `${slug}.mp4`;
    const videoPath     = path.join(outDir, videoFilename);
    let downloaded = false;

    // A: yt-dlp
    const ytdlp = spawnSync(
      'yt-dlp',
      ['-f', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]',
       '--merge-output-format', 'mp4', '--no-warnings', '--quiet', '-o', videoPath, href],
      { timeout: 600_000, stdio: 'pipe' }
    );
    if (ytdlp.status === 0 && fs.existsSync(videoPath)) {
      results.push({ lecture: text.slice(0, 35), type: 'video', lang: '720p', file: videoFilename, status: `✓ ${humanSize(fs.statSync(videoPath).size)} (yt-dlp)` });
      downloaded = true;
    }

    // B: DOM src
    if (!downloaded) {
      const domSrcs = await page.evaluate(() => {
        const vid = document.querySelector('video');
        const srcs = [];
        if (vid?.src) srcs.push(vid.src);
        for (const s of vid?.querySelectorAll('source') ?? []) if (s.src) srcs.push(s.src);
        for (const sc of document.querySelectorAll('script:not([src])')) {
          const m = sc.textContent.match(/https?:\/\/[^"'\s]+\.mp4[^"'\s]*/g) ?? [];
          srcs.push(...m);
        }
        return srcs;
      });
      const src = domSrcs.find((u) => u.includes('720')) || domSrcs.find((u) => u.includes('540')) || domSrcs[0];
      if (src) {
        try {
          const bytes = await downloadUrl(src, videoPath);
          results.push({ lecture: text.slice(0, 35), type: 'video', lang: '720p', file: videoFilename, status: `✓ ${humanSize(bytes)} (dom)` });
          downloaded = true;
        } catch { /* fall through */ }
      }
    }

    // C: network intercept
    if (!downloaded) {
      const captured = [];
      const onReq = (req) => {
        const u = req.url();
        if ((u.includes('.mp4') || u.includes('.m3u8')) && !captured.includes(u)) captured.push(u);
      };
      page.on('request', onReq);
      await page.reload(); await new Promise((r) => setTimeout(r, delay + 2000));
      page.off('request', onReq);

      const src = captured.find((u) => u.includes('720')) || captured.find((u) => u.includes('540')) || captured[0];
      if (src) {
        if (src.includes('.m3u8')) {
          const ff = spawnSync('ffmpeg', ['-y', '-i', src, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', videoPath], { timeout: 600_000, stdio: 'pipe' });
          if (ff.status === 0 && fs.existsSync(videoPath)) {
            results.push({ lecture: text.slice(0, 35), type: 'video', lang: '720p', file: videoFilename, status: `✓ ${humanSize(fs.statSync(videoPath).size)} (hls)` });
            downloaded = true;
          }
        } else {
          try {
            const bytes = await downloadUrl(src, videoPath);
            results.push({ lecture: text.slice(0, 35), type: 'video', lang: '720p', file: videoFilename, status: `✓ ${humanSize(bytes)} (intercept)` });
            downloaded = true;
          } catch { /* fall through */ }
        }
      }
    }

    if (!downloaded)
      results.push({ lecture: text.slice(0, 35), type: 'video', lang: '720p', file: '—', status: '✗ no video source' });

    // ── Supplementary resources (PDFs, slides, background reading) ─────────
    if (resources) {
      const resLinks = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href]'))
          .map(a => {
            const href = a.href;
            const txt = a.textContent.trim();
            const isCDN = href.includes('cloudfront.net') || href.includes('coursera.org/asset');
            const isPDF = href.includes('.pdf') || txt.toLowerCase().startsWith('pdf');
            const isDoc = /\.(doc|pptx?|xlsx?|zip)$/i.test(href) || txt.toLowerCase().startsWith('doc');
            const isVideo = href.includes('.mp4') || href.includes('.m3u8') || txt.toLowerCase().startsWith('mp4');
            const isSub = href.includes('.vtt') || href.includes('.srt');
            if (isCDN && (isPDF || isDoc) && !isVideo && !isSub) {
              const urlMatch = href.match(/[^/]+$/);
              const rawName = urlMatch ? urlMatch[0].split('?')[0] : txt;
              const cleanName = rawName.replace(/^_[a-f0-9]+_/, '').replace(/^[a-f0-9]{20,}_/, '');
              return { text: txt, href, filename: cleanName || rawName };
            }
            return null;
          })
          .filter(Boolean)
      );

      const seen = new Set();
      for (const res of resLinks) {
        if (seen.has(res.href)) continue;
        seen.add(res.href);
        const resFilename = `${slug}_${res.filename}`;
        const resPath = path.join(outDir, resFilename);
        try {
          const bytes = await downloadUrl(res.href, resPath);
          results.push({ lecture: text.slice(0, 35), type: 'resource', lang: '—', file: resFilename, status: `✓ ${humanSize(bytes)}` });
        } catch (e) {
          results.push({ lecture: text.slice(0, 35), type: 'resource', lang: '—', file: resFilename, status: `✗ ${String(e.message).slice(0, 40)}` });
        }
      }
    }
  }
}

// ─── adapter ──────────────────────────────────────────────────────────────────

cli({
  site: 'coursera',
  name: 'download',
  description:
    'Download subtitles (default: en › zh-CN › zh-TW), optional 720p video, and supplementary resources (PDFs, slides). ' +
    'Accepts a course home URL (auto-discovers all modules) or a single module URL. ' +
    'Locale-independent. Requires a Chrome session logged in to coursera.org.',
  access: 'read',
  example:
    'opencli coursera download "https://www.coursera.org/learn/introduction-to-model-context-protocol" --out ./mcp --locale en',
  domain: 'coursera.org',
  strategy: Strategy.COOKIE,
  browser: true,
  args: [
    {
      name: 'url', positional: true, type: 'string', required: true,
      help: 'Course home URL (.../learn/COURSE) or module URL (.../home/module/N). ' +
            'Course home → auto-discovers and downloads ALL modules.',
    },
    { name: 'out',    type: 'string', default: './coursera-dl', help: 'Output root directory' },
    {
      name: 'langs', type: 'string', default: 'en,zh-CN,zh-TW',
      help: 'Subtitle languages in priority order. All listed & available languages are downloaded. ' +
            'Use "all" for every language. Examples: "en"  "en,ja"  "zh-CN,en"',
    },
    {
      name: 'locale', type: 'string', default: '',
      help: 'Force Coursera UI language via ?hl= (e.g. "en"). Subtitle content is locale-independent.',
    },
    { name: 'video',     type: 'bool',   default: false, help: 'Also download 720p video' },
    { name: 'resources', type: 'bool',   default: false, help: 'Download supplementary resources (PDFs, slides, background reading)' },
    { name: 'delay',  type: 'int',    default: 4000,  help: 'Page load wait in ms (increase on slow connections)' },
  ],
  columns: ['module', 'lecture', 'type', 'lang', 'file', 'status'],

  func: async (page, kwargs) => {
    const { url, out, langs, locale, video, resources, delay } = kwargs;

    const downloadAll = langs.trim().toLowerCase() === 'all';
    const langList = downloadAll ? [] : langs.split(',').map((l) => l.trim()).filter(Boolean);

    const results = [];
    const urlType = detectUrlType(url);

    // ── Resolve module list ────────────────────────────────────────────────────
    let modules; // [{ num, href, text }]

    if (urlType.type === 'module') {
      // Single module mode — no discovery needed
      modules = [{ num: urlType.moduleNum, href: url.split('?')[0], text: `Module ${urlType.moduleNum}` }];
    } else {
      // Course home mode — discover all modules from welcome page
      console.error('[coursera-dl] Course URL detected → discovering modules…');
      modules = await discoverModules(page, url, locale, delay);

      if (!modules.length) {
        return [{ module: '—', lecture: '—', type: '—', lang: '—', file: '—', status: '✗ No modules found on welcome page. Check URL and login.' }];
      }
      console.error(`[coursera-dl] Found ${modules.length} module(s): ${modules.map((m) => `Module ${m.num}`).join(', ')}`);
    }

    // ── Download each module ───────────────────────────────────────────────────
    for (const mod of modules) {
      const moduleLabel = `M${mod.num}`;
      const outDir = modules.length === 1
        ? out                                          // single module → write directly to --out
        : path.join(out, `module-${mod.num}`);        // multi-module  → subdirectory per module

      // Inject module column into results as a section header row
      const moduleResults = [];
      await downloadModule(page, {
        moduleUrl: mod.href,
        outDir,
        langList,
        downloadAll,
        locale,
        video,
        resources,
        delay,
        results: moduleResults,
      });

      // Tag each row with the module label
      for (const row of moduleResults) {
        results.push({ module: moduleLabel, ...row });
      }

      if (!moduleResults.length) {
        results.push({ module: moduleLabel, lecture: '—', type: '—', lang: '—', file: '—', status: '⚠ No lectures found in this module' });
      }
    }

    return results;
  },
});
