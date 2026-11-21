// Slate website: scroll-driven ASCII rocks (same data the OS uses for its wallpapers and
// welcome animation: branding/ascii_rocks.py -> /usr/share/slate/rocks/*.json).
(() => {
  const LIME = [182, 242, 58], BG = [17, 18, 20];
  const GLYPHS = '#%@*+=-:./\\|_^';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const shade = s => {
    s = clamp(s);
    return `rgb(${BG.map((b, i) => Math.round(b + (LIME[i] - b) * s)).join(',')})`;
  };
  // deterministic pseudo-random per cell
  const hash = (x, y, k = 0) => { let h = (x * 374761393 + y * 668265263 + k * 1442695041) | 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

  // scroll progress of a tall section whose child is sticky: 0 at top, 1 when it leaves
  const progress = el => {
    const r = el.getBoundingClientRect(), span = r.height - innerHeight;
    return span > 0 ? clamp(-r.top / span) : 1;
  };

  function sizeCanvas(cv, rock, fill) {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const w = cv.clientWidth;
    const cw = w / rock.cols;               // cell width
    const fs = cw / 0.602, ch = fs * 1.17;  // Hack: advance 0.602em
    const h = Math.ceil(ch * rock.rows);
    cv.style.height = h + 'px';
    cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.font = `${fs}px Hack, ui-monospace, monospace`;
    g.textBaseline = 'top';
    return { g, cw, ch, w, h };
  }

  // draw cells; pick(x, y) -> [char, shade] or null
  function draw(ctx, rock, pick) {
    const { g, cw, ch, w, h } = ctx;
    g.clearRect(0, 0, w, h);
    const buckets = new Map();
    for (let y = 0; y < rock.rows; y++) for (let x = 0; x < rock.cols; x++) {
      const c = pick(x, y); if (!c || c[0] === ' ') continue;
      const k = Math.round(clamp(c[1]) * 24);
      if (!buckets.has(k)) buckets.set(k, []);
      buckets.get(k).push(x, y, c[0]);
    }
    for (const [k, list] of buckets) {
      g.fillStyle = shade(k / 24);
      for (let i = 0; i < list.length; i += 3) g.fillText(list[i + 2], list[i] * cw, list[i + 1] * ch);
    }
  }

  Promise.all(['assets/basalt.json', 'assets/agate.json'].map(u => fetch(u).then(r => r.json())))
    .then(([basalt, agate]) => (document.fonts ? document.fonts.load('16px Hack') : Promise.resolve())
      .then(() => start(basalt, agate)));

  function start(basalt, agate) {
    // ---------- hero: columns rise from the ground as you scroll ----------
    const hero = document.getElementById('hero'), heroCv = document.getElementById('heroRock');
    const heroText = document.querySelector('.hero-text'), hint = document.getElementById('scrollHint');
    const rise = [];   // reveal threshold per cell (bottom rows first)
    for (let y = 0; y < basalt.rows; y++) for (let x = 0; x < basalt.cols; x++)
      rise.push((1 - y / basalt.rows) * 0.8 + hash(x, y) * 0.12 + 0.04 * Math.sin(x / 6));
    let heroCtx, introP = 0;
    const t0 = performance.now();
    const intro = now => {
      introP = 0.35 * clamp((now - t0) / 1600) ** 0.7;
      drawHero();
      if (introP < 0.35) requestAnimationFrame(intro);
    };
    heroText.classList.add('on');
    const drawHero = () => {
      // on load the columns rise a third of the way by themselves; scrolling raises the rest
      const sp = clamp(progress(hero) / 0.75);
      const p = reduce ? 1 : Math.max(introP, sp > 0 ? 0.35 + 0.65 * sp : 0);
      draw(heroCtx, basalt, (x, y) => {
        const c = basalt.text[y][x]; if (c === ' ') return null;
        const t = rise[y * basalt.cols + x], d = p - t;
        if (d < -0.05) return null;
        if (d < 0) return [GLYPHS[Math.floor(hash(x, y, Math.floor(p * 60)) * GLYPHS.length)], 0.3];
        return [c, basalt.shade[y][x] * (0.55 + 0.45 * clamp(1 - p * 0.6))];   // dim behind the title
      });
      hint.style.opacity = sp > 0.05 ? 0 : 1;
    };

    // ---------- releases: Agate morphs into Basalt ----------
    const rel = document.getElementById('releases'), morphCv = document.getElementById('morphRock');
    const items = [...document.querySelectorAll('.rel-list li[data-at]')];
    const cx = agate.cols / 2, cy = agate.rows / 2;
    const morphT = [];
    for (let y = 0; y < agate.rows; y++) for (let x = 0; x < agate.cols; x++)
      morphT.push(clamp(Math.hypot((x - cx) / cx, (y - cy) / cy) / 1.5) * 0.7 + hash(x, y, 9) * 0.3);
    let morphCtx;
    const drawMorph = () => {
      const p = reduce ? 1 : clamp((progress(rel) - 0.2) / 0.55);
      draw(morphCtx, agate, (x, y) => {
        const t = morphT[y * agate.cols + x], d = p - t;
        if (d < -0.04) { const c = agate.text[y][x]; return c === ' ' ? null : [c, agate.shade[y][x]]; }
        if (d < 0.04) return [GLYPHS[Math.floor(hash(x, y, Math.floor(p * 80)) * GLYPHS.length)], 0.35];
        const c = basalt.text[y][x]; return c === ' ' ? null : [c, basalt.shade[y][x]];
      });
      const stage = p < 0.5 ? 0 : 1;
      items.forEach(li => li.classList.toggle('on', +li.dataset.at === stage));
    };

    const resize = () => {
      heroCtx = sizeCanvas(heroCv, basalt);
      morphCtx = sizeCanvas(morphCv, agate);
      drawHero(); drawMorph();
    };
    let queued = false;
    addEventListener('scroll', () => {
      if (queued) return; queued = true;
      requestAnimationFrame(() => { queued = false; drawHero(); drawMorph(); });
    }, { passive: true });
    addEventListener('resize', resize);
    resize();
    if (!reduce) requestAnimationFrame(intro);
    // screenshots/testing: index.html#y=1200 opens scrolled to that position
    const m = location.hash.match(/^#y=(\d+)/);
    if (m) { document.documentElement.style.scrollBehavior = 'auto'; scrollTo(0, +m[1]); }
  }

  // ---------- fade-in on scroll + terminal typing ----------
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in'); io.unobserve(e.target);
    if (e.target.classList.contains('term')) typeTerminal();
  }), { threshold: 0.2 });
  document.querySelectorAll('.reveal, .shelf-demo').forEach(el => io.observe(el));

  function typeTerminal() {
    const out = document.getElementById('termOut');
    fetch('assets/basalt-logo.txt').then(r => r.text()).then(txt => {
      const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
      // fastfetch logo format: $1 $2 $3 switch color, $$ is a literal $
      const logo = txt.replace(/\n$/, '').split('\n').map(line => {
        let html = '', cls = 'l1';
        line.split(/(\$[123$])/).forEach(part => {
          if (/^\$[123]$/.test(part)) cls = 'l' + part[1];
          else if (part === '$$') html += '$';
          else if (part) html += `<span class="${cls}">${esc(part)}</span>`;
        });
        return { html, len: line.replace(/\$[123]/g, '').replace(/\$\$/g, '$').length };
      });
      const info = [
        '<span class="k">slate</span>@<span class="k">slate</span>', '-----------',
        '<span class="k">OS</span>  Slate 0.2 (Basalt) x86_64', '<span class="k">Kernel</span>  6.12 (Debian 13)',
        '<span class="k">Packages</span>  2104 (dpkg)', '<span class="k">DE</span>  KDE Plasma 6.3',
        '<span class="k">WM</span>  KWin (Wayland)', '<span class="k">Terminal</span>  konsole',
        '<span class="k">Font</span>  Hack 11', '', '<span class="l1">●</span> <span class="l2">●</span> <span class="l3">●</span> ●'];
      const width = Math.max(...logo.map(l => l.len)) + 3;
      const rows = Math.max(logo.length, info.length + 1);
      const lines = [];
      for (let i = 0; i < rows; i++) {
        const l = logo[i] || { html: '', len: 0 };
        const inf = info[i - 1] || '';
        lines.push(l.html + ' '.repeat(width - l.len) + inf);
      }
      let n = 0;
      const step = () => {
        out.innerHTML = '<span class="p">$</span> slate\n' + lines.slice(0, n).join('\n');
        if (n++ < lines.length) setTimeout(step, reduce ? 0 : 55);
      };
      setTimeout(step, reduce ? 0 : 400);
    });
  }
})();
