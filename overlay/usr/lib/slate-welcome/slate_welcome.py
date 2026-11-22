#!/usr/bin/python3
"""Slate welcome: the release's ASCII rock assembles on screen, then quick setup cards.

  slate-welcome            full welcome (animation + cards)
  slate-welcome --auto     from autostart: full welcome on first login, animation + "what's
                           new" once after each Slate version upgrade, otherwise nothing
  slate-welcome --whatsnew animation + what's new
  slate-welcome --patch    no animation: notes for this release's point updates (0.2.1, 0.2.2, ...)

Point updates (a new slate-desktop version within the same VERSION_ID) don't replay the
animation: --auto shows a notification with a "What's new" button instead, once per update
that ships notes in /usr/share/slate/releases/<version>.md.
"""
import configparser, glob, json, math, os, random, subprocess, sys, time
from PyQt6.QtCore import (QObject, QProcess, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot)
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6 import QtQuick  # noqa: F401  (root objects come back as QQuickWindow)

HERE = os.path.dirname(os.path.abspath(__file__))
TEST_ROOT = os.environ.get('SLATE_TEST_ROOT', '')   # dev: run against an unpacked overlay
SHARE = TEST_ROOT + '/usr/share/slate'
CONF = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'slate-welcomerc')
LIME = (0xb6, 0xf2, 0x3a); BG = (0x11, 0x12, 0x14)
ACCENTS = [('Lime', '#b6f23a'), ('Cyan', '#3ad6f2'), ('Orange', '#f2a33a'), ('Violet', '#a98bf5')]
GLYPHS = '#%@*+=-:./\\|_^'


def os_release(path=os.environ.get('SLATE_OS_RELEASE', '/etc/os-release')):
    d = {}
    try:
        for line in open(path):
            if '=' in line and not line.startswith('#'):
                k, v = line.rstrip('\n').split('=', 1); d[k] = v.strip('"')
    except OSError:
        pass
    return d


def read_conf():
    c = configparser.ConfigParser(); c.optionxform = str
    try: c.read(CONF)
    except configparser.Error: pass
    return c


def mark_seen(version, patch=None):
    c = read_conf()
    if not c.has_section('General'): c.add_section('General')
    c.set('General', 'LastSeenVersion', version)
    if patch: c.set('General', 'LastSeenPatch', patch)
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    with open(CONF, 'w') as f: c.write(f)


def has_facetime_camera():
    for dev in glob.glob('/sys/bus/pci/devices/*'):
        try:
            if open(dev + '/vendor').read().strip() == '0x14e4' and \
               open(dev + '/device').read().strip() == '0x1570':
                return True
        except OSError:
            pass
    return False


def pkg_version():
    """Installed slate-desktop version, e.g. '0.2.3' (empty when unknown)."""
    v = os.environ.get('SLATE_PKG_VERSION')
    if v is not None: return v
    try:
        return subprocess.run(['dpkg-query', '-W', '-f=${Version}', 'slate-desktop'],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def vkey(v):
    return tuple(int(p) if p.isdigit() else 0 for p in v.replace('-', '.').split('.'))


def patch_notes(release):
    """[(version, markdown)] for this release's point updates, newest first."""
    out = []
    for f in glob.glob(os.path.join(SHARE, 'releases', release + '.*.md')):
        v = os.path.basename(f)[:-3]
        try: out.append((v, open(f).read()))
        except OSError: pass
    return sorted(out, key=lambda n: vkey(n[0]), reverse=True)


def notify_patch(patch, notes):
    """Desktop notification for a point update; its button opens the patch notes."""
    body = next((l.strip('-* ').strip() for l in notes.splitlines()
                 if l.strip() and not l.startswith('#')), 'Fixes and improvements.')
    try:
        r = subprocess.run(['notify-send', '--app-name=Slate', '--icon=slate-shale',
                            "--action=notes=What's new", f'Slate updated to {patch}', body],
                           capture_output=True, text=True)
    except OSError:
        return 0
    if r.stdout.strip() == 'notes':
        os.execvp(sys.executable, [sys.executable, os.path.abspath(__file__), '--patch'])
    return 0


def has_camera_driver():
    return os.path.exists(TEST_ROOT + '/usr/sbin/slate-facetimehd-firmware')


def is_live():
    try: return 'boot=live' in open('/proc/cmdline').read()
    except OSError: return False


def color(s):
    s = max(0.0, min(1.0, s))
    return '#%02x%02x%02x' % tuple(int(b + (f - b) * s) for b, f in zip(BG, LIME))


class Backend(QObject):
    frameChanged = pyqtSignal()
    introDoneChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, mode):
        super().__init__()
        rel = os_release()
        self._version = rel.get('VERSION_ID', '0.2')
        self._name = (rel.get('SLATE_CODENAME') or 'basalt').capitalize()
        self._mode = mode
        self._camera = has_facetime_camera() and not is_live() and not has_camera_driver()
        self._live = is_live()
        self._status = ''
        self._accent = None
        self._queue = []; self._proc = None
        self.load_rock()
        self._intro_done = False
        self._t0 = time.monotonic()
        self._timer = QTimer(self); self._timer.timeout.connect(self.tick); self._timer.start(33)

    # ---- the ASCII rock animation ----
    def load_rock(self):
        path = os.path.join(SHARE, 'rocks', self._name.lower() + '.json')
        if not os.path.exists(path):
            files = sorted(glob.glob(os.path.join(SHARE, 'rocks', '*.json')))
            path = files[-1] if files else None
        data = json.load(open(path)) if path else {'cols': 1, 'rows': 1, 'text': [' '], 'shade': [[0]]}
        self._cols, self._rows = data['cols'], data['rows']
        self._text, self._shade = data['text'], data['shade']
        rnd = random.Random(7)
        self._reveal = []
        radial = data.get('name', self._name).lower() == 'agate'
        for y in range(self._rows):
            row = []
            for x in range(self._cols):
                if radial:      # agate: grows outward from the crystal cavity
                    r = math.hypot((x - self._cols / 2) / (self._cols / 2), (y - self._rows / 2) / (self._rows / 2))
                    t = r * 2.0
                else:           # basalt (and default): columns rise from the ground up
                    t = (1 - y / self._rows) * 2.0 + 0.25 * math.sin(x / 6.0)
                row.append(max(0.0, t + rnd.uniform(0, 0.35)))
            self._reveal.append(row)
        self._end = max(max(r) for r in self._reveal) + 0.4
        self._frame = [''] * self._rows
        self._rnd = rnd

    def row_markup(self, y, now):
        out = []; cur = None; buf = ''
        for x, ch in enumerate(self._text[y]):
            # blanks are drawn as background-colored dots: rich text drops leading spaces
            if ch == ' ':
                c, s = '.', 0.0
            else:
                dt = now - self._reveal[y][x]
                if dt < 0:
                    c, s = '.', 0.0
                elif dt < 0.35:          # flicker through random glyphs, then settle
                    c, s = self._rnd.choice(GLYPHS), 0.25 + dt
                else:
                    c, s = ch, self._shade[y][x]
            col = None if s is None else color(s)
            if c in '&<>':
                c = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]
            if col != cur:
                if buf: out.append(buf if cur is None else f'<font color="{cur}">{buf}</font>')
                buf = ''; cur = col
            buf += c
        if buf: out.append(buf if cur is None else f'<font color="{cur}">{buf}</font>')
        return ''.join(out)

    def tick(self):
        now = time.monotonic() - self._t0
        if now >= self._end:
            now = 1e9
        self._frame = [self.row_markup(y, now) for y in range(self._rows)]
        self.frameChanged.emit()
        if now == 1e9:
            self._timer.stop()
            if not self._intro_done:
                self._intro_done = True; self.introDoneChanged.emit()

    @pyqtSlot()
    def skipIntro(self):
        self._t0 -= 100; self.tick()

    @pyqtProperty(list, notify=frameChanged)
    def frame(self): return self._frame
    @pyqtProperty(int, constant=True)
    def cols(self): return self._cols
    @pyqtProperty(int, constant=True)
    def rows(self): return self._rows
    @pyqtProperty(bool, notify=introDoneChanged)
    def introDone(self): return self._intro_done
    @pyqtProperty(str, constant=True)
    def version(self): return self._version
    @pyqtProperty(str, constant=True)
    def releaseName(self): return self._name
    @pyqtProperty(str, constant=True)
    def mode(self): return self._mode
    @pyqtProperty(bool, constant=True)
    def hasCamera(self): return self._camera
    @pyqtProperty(bool, constant=True)
    def live(self): return self._live
    @pyqtProperty(int, constant=True)
    def startPage(self):    # patch notes skip the animation; dev/testing: open at a card
        if self._mode == 'patch': return 0
        return int(os.environ.get('SLATE_WELCOME_PAGE', '-1'))
    @pyqtProperty(str, notify=statusChanged)
    def status(self): return self._status
    @pyqtProperty(str, constant=True)
    def logo(self):    # transparent PNG wordmark (made by branding/build-assets.py)
        return QUrl.fromLocalFile(TEST_ROOT + '/usr/share/plasma/look-and-feel/org.slate.desktop/'
                                  'contents/splash/images/slate-wordmark.png').toString()
    @pyqtSlot(str, result=str)
    def shale(self, face):   # Shale the hermit crab in this release's rock shell
        f = os.path.join(SHARE, 'shale', f'{self._name.lower()}-{face}.png')
        return QUrl.fromLocalFile(f).toString() if os.path.exists(f) else ''
    @pyqtProperty(str, constant=True)
    def whatsNew(self):
        if self._mode == 'patch':
            notes = patch_notes(self._version)
            return '\n\n'.join(n for _v, n in notes) or 'Fixes and improvements.'
        try: return open(os.path.join(SHARE, 'releases', self._version + '.md')).read()
        except OSError: return f'Slate {self._version} {self._name}.'
    @pyqtProperty(str, constant=True)
    def whatsNewTitle(self):
        if self._mode == 'patch':
            return "What's new in " + (pkg_version() or self._version)
        return "What's new in " + self._name
    @pyqtProperty(list, constant=True)
    def accents(self): return [{'name': n, 'color': c} for n, c in ACCENTS]
    @pyqtProperty(list, constant=True)
    def wallpapers(self):
        out = []
        for d in sorted(glob.glob(TEST_ROOT + '/usr/share/wallpapers/Slate*/')):
            pid = os.path.basename(d.rstrip('/'))
            try: name = json.load(open(d + 'metadata.json'))['KPlugin']['Name']
            except (OSError, ValueError, KeyError): name = pid
            out.append({'id': pid, 'name': name, 'path': d.rstrip('/'),
                        'thumb': QUrl.fromLocalFile(d + 'contents/screenshot.png').toString()})
        cur = f'Slate-{self._name}'          # newest rock first
        out.sort(key=lambda w: (w['id'] != cur, w['id']))
        return out
    @pyqtProperty(str, constant=True)
    def currentRockWallpaper(self): return f'/usr/share/wallpapers/Slate-{self._name}'
    @pyqtProperty(str, constant=True)
    def themePreviewDark(self):
        return QUrl.fromLocalFile(TEST_ROOT + '/usr/share/plasma/look-and-feel/org.slate.desktop/contents/previews/preview.png').toString()
    @pyqtProperty(str, constant=True)
    def themePreviewLight(self):
        return QUrl.fromLocalFile(TEST_ROOT + '/usr/share/plasma/look-and-feel/org.slate.light.desktop/contents/previews/preview.png').toString()

    # ---- applying choices (run one after another, in the background) ----
    def run(self, *cmd):
        self._queue.append(list(cmd)); self._next()

    def _next(self):
        if self._proc or not self._queue: return
        cmd = self._queue.pop(0)
        self._proc = QProcess(self)
        self._proc.finished.connect(self._done)
        self._proc.errorOccurred.connect(lambda _e: self._done())
        self._proc.start(cmd[0], cmd[1:])

    def _done(self, *a):
        if self._proc:
            self._proc.deleteLater(); self._proc = None
        self._next()

    @pyqtSlot(str)
    def setTheme(self, which):
        self.run('plasma-apply-lookandfeel', '-a',
                 'org.slate.light.desktop' if which == 'light' else 'org.slate.desktop')
        if self._accent:   # a look-and-feel switch brings its own colors; keep the chosen accent
            self.run('plasma-apply-colorscheme', '--accent-color', self._accent)

    @pyqtSlot(str)
    def setAccent(self, col):
        self._accent = col
        self.run('plasma-apply-colorscheme', '--accent-color', col)

    @pyqtSlot(str)
    def setWallpaper(self, path):
        self.run('plasma-apply-wallpaperimage', path)
        self.run('kwriteconfig6', '--file', 'kscreenlockerrc', '--group', 'Greeter', '--group', 'Wallpaper',
                 '--group', 'org.kde.image', '--group', 'General', '--key', 'Image', 'file://' + path + '/')

    @pyqtSlot()
    def installCamera(self):
        self._status = 'installing'; self.statusChanged.emit()
        p = QProcess(self)
        def fin(code, _st=None):
            self._status = 'done' if code == 0 else 'failed'; self.statusChanged.emit()
        p.finished.connect(fin)
        # pkexec missing or not runnable: finished never fires, so report failure here
        p.errorOccurred.connect(lambda e: e == QProcess.ProcessError.FailedToStart and fin(1))
        p.start('pkexec', ['sh', '-c', 'apt-get update && DEBIAN_FRONTEND=noninteractive '
                                       'apt-get install -y slate-facetimehd'])

    @pyqtSlot()
    def finish(self):
        mark_seen(self._version, pkg_version())
        QGuiApplication.quit()


def main():
    args = sys.argv[1:]
    rel = os_release(); ver = rel.get('VERSION_ID', '0.2')
    mode = 'full'
    if '--whatsnew' in args:
        mode = 'update'
    elif '--patch' in args:
        mode = 'patch'
    elif '--auto' in args:
        conf = read_conf()
        last = conf.get('General', 'LastSeenVersion', fallback='')
        if last == ver:     # same release: maybe a point update with notes to announce
            patch = pkg_version()
            seen = conf.get('General', 'LastSeenPatch', fallback='')
            notes = dict(patch_notes(ver))
            if patch and patch != seen and patch in notes:
                mark_seen(ver, patch)
                return notify_patch(patch, notes[patch])
            return 0
        mode = 'update' if last else 'full'
    if '--auto' in args:
        time.sleep(4)   # let Plasma restore the last session's windows first, then open on top
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName('slate-welcome'); app.setDesktopFileName('slate-welcome')
    app.setWindowIcon(QIcon.fromTheme('slate-launcher'))
    backend = Backend(mode)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('backend', backend)
    engine.load(QUrl.fromLocalFile(os.path.join(HERE, 'qml', 'Main.qml')))
    if not engine.rootObjects():
        return 1
    win = engine.rootObjects()[0]
    win.raise_(); win.requestActivate()
    if '--auto' in args:     # once more, in case restored windows were still opening
        QTimer.singleShot(3000, lambda: (win.raise_(), win.requestActivate()))
    shot = os.environ.get('SLATE_WELCOME_SHOT')    # dev: save screenshots, e.g. "/tmp/w:3,5"
    if shot:
        base, _, times = shot.partition(':')
        for i, t in enumerate(float(x) for x in times.split(',')):
            QTimer.singleShot(int(t * 1000), lambda i=i: win.grabWindow().save(f'{base}{i}.png'))
        QTimer.singleShot(int(max(float(x) for x in times.split(',')) * 1000) + 300, app.quit)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
