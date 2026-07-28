/**
 * mooc.js — Universal MOOC download dispatcher
 * Part of mooc2handout-skill multi-platform pipeline.
 *
 * Detects the MOOC platform from the URL and delegates to the
 * appropriate opencli adapter (coursera, edx, futurelearn, etc.)
 *
 * Usage:
 *   node mooc.js "https://www.coursera.org/learn/COURSE" --video --resources
 *   node mooc.js "https://www.edx.org/course/..." --video
 *
 * Or via opencli (if registered):
 *   opencli mooc download "URL" --video --resources
 */

import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Platform detection ────────────────────────────────────────────────────────

const PLATFORMS = [
  {
    name: 'coursera',
    patterns: [/coursera\.org/],
    adapter: 'adapters/coursera.js',
    site: 'coursera',
    command: 'download',
  },
  // Future platforms:
  // {
  //   name: 'edx',
  //   patterns: [/edx\.org/, /2u\.com/],
  //   adapter: 'adapters/edx.js',
  //   site: 'edx',
  //   command: 'download',
  // },
  // {
  //   name: 'futurelearn',
  //   patterns: [/futurelearn\.com/],
  //   adapter: 'adapters/futurelearn.js',
  //   site: 'futurelearn',
  //   command: 'download',
  // },
];

function detectPlatform(url) {
  for (const p of PLATFORMS) {
    if (p.patterns.some(re => re.test(url))) {
      return p;
    }
  }
  return null;
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    console.log(`
mooc2handout — Universal MOOC download dispatcher

Usage:
  node mooc.js "<MOOC_URL>" [options]

Options:
  --video          Also download 720p video
  --resources      Download supplementary materials (PDFs, slides)
  --out <dir>      Output directory (default: ./mooc-dl)
  --langs <list>   Subtitle languages (default: en,zh-CN,zh-TW)
  --locale <lang>  Force UI language
  --delay <ms>     Page load wait (default: 4000)

Supported platforms:
  Coursera        coursera.org          (full support)
  edX             edx.org               (planned)
  FutureLearn     futurelearn.com       (planned)

Examples:
  node mooc.js "https://www.coursera.org/learn/mathematical-thinking" --video --resources
  node mooc.js "https://www.coursera.org/learn/COURSE/home/module/1" --out ./m1
`);
    process.exit(0);
  }

  const url = args[0];
  const platform = detectPlatform(url);

  if (!platform) {
    console.error(`Error: Unsupported platform for URL: ${url}`);
    console.error(`Supported: ${PLATFORMS.map(p => p.name).join(', ')}`);
    console.error(`\nTo add a new platform, create an adapter in skill/adapters/`);
    process.exit(1);
  }

  console.error(`[mooc] Detected platform: ${platform.name}`);
  console.error(`[mooc] Using adapter: ${platform.adapter}`);

  // Check if opencli adapter is installed
  const adapterPath = path.join(__dirname, platform.adapter);
  const opencliAdapterDir = path.join(
    process.env.HOME || process.env.USERPROFILE || '~',
    '.opencli', 'clis', platform.site
  );
  const installedPath = path.join(opencliAdapterDir, 'download.js');

  // Check if adapter needs installation
  const fs = await import('fs');
  if (!fs.default.existsSync(installedPath)) {
    console.error(`[mooc] Installing adapter to ${installedPath}...`);
    fs.default.mkdirSync(opencliAdapterDir, { recursive: true });
    fs.default.copyFileSync(adapterPath, installedPath);
    console.error(`[mooc] Adapter installed.`);
  }

  // Build opencli command args
  const cliArgs = [platform.site, platform.command, url, ...args.slice(1)];
  console.error(`[mooc] Running: opencli ${cliArgs.join(' ')}`);

  const result = spawnSync('opencli', cliArgs, {
    stdio: 'inherit',
    timeout: 600_000,
  });

  process.exit(result.status ?? 1);
}

main();
