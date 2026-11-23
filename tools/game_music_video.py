"""Gameplay music-video pipeline (game-music-video workflow): vendor, dry-run, record, sheet.

The engine runtime is 3d/godot/music_video/music_video_recorder.gd. A game extends it with an adapter and
per-song shot lists (see workflows/game-music-video/README.md). This tool never edits game code and never
touches saves; the recorder script is responsible for disabling saving.

  vendor   Copy the Godot recorder into a game project with a SHA-256 lock.
  dry-run  Run one song headless (fast, no picture): completion, shot count, blocked-camera shots, errors.
  record   Movie Maker capture at a chosen window size, then trim to the song start, mix the exact song file
           over the recorded game effects (no normalization), encode H.264/AAC, a sharing preview and a contact sheet.
  sheet    Contact sheet of an existing video.

GPU safety (Windows): record and showcase refuse to start when the display driver has reset since the last boot
(System log, provider Display, event 4101 "stopped responding and has recovered" or 4109 "blocked from accessing
graphics hardware"). A recovered driver can leave the graphics stack half-working, and more GPU work on it has hung
the whole PC. Reboot first, or pass --allow-after-gpu-reset. The refusal exits with code 3 so batch scripts can stop.

Examples (from the GameCore root):
  python tools/game_music_video.py vendor --project X:/Projects/MyGame/game
  python tools/game_music_video.py dry-run --godot <Godot_console.exe> --project X:/Projects/MyGame/game \
      --script X:/Projects/MyGame/Design/music-videos/record.gd --song theme
  python tools/game_music_video.py record --godot <exe> --project <game> --script <record.gd> --song theme \
      --audio X:/Projects/MyGame/game/assets/audio/theme.mp3 --out X:/Projects/MyGame/Design/music-videos
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '3d/godot/music_video/music_video_recorder.gd'
DEFAULT_DEST = 'addons/gamecore_music_video'
LOCK_NAME = 'gamecore_music_video.lock.json'
# Vendorable Godot modules: the recorder (+ asset showcase base) and the world-life kit.
MODULES = {
    'music-video': {'id': 'gamecore.godot.music-video-recorder', 'dest': DEFAULT_DEST, 'lock': LOCK_NAME,
                    'files': ['3d/godot/music_video/music_video_recorder.gd', '3d/godot/music_video/asset_showcase.gd']},
    'world-life': {'id': 'gamecore.godot.world-life-kit', 'dest': 'addons/gamecore_world_life', 'lock': 'gamecore_world_life.lock.json',
                   'files': ['3d/godot/world_life/world_life_kit.gd', '3d/godot/world_life/sea_breach.gd', '3d/godot/world_life/splash_pool.gd',
                             '3d/godot/world_life/beat_dance.gd', '3d/godot/world_life/attention_glance.gd', '3d/godot/world_life/idle_scheduler.gd',
                             '3d/godot/world_life/escort_formation.gd', '3d/godot/world_life/proximity_notes.gd', '3d/godot/world_life/time_of_day.gd',
                             '3d/godot/world_life/ambient_chatter.gd', '3d/godot/world_life/route_gates.gd', '3d/godot/world_life/celebration_burst.gd',
                             '3d/godot/world_life/flutter_motion.gd','3d/godot/world_life/flutter_swarm.gd',
                             '3d/godot/world_life/wing_patterns.gd','3d/godot/world_life/timed_stroke_track.gd',
                             '3d/godot/world_life/painting_coverage.gd','3d/godot/world_life/sand_reveal.gd',
                             '3d/godot/world_life/companion_follow.gd',
                             '3d/godot/world_life/terrain_ring_clearance.gd','3d/godot/world_life/timed_cue_cursor.gd']},
}
OVERRIDE_DIR = '.gamecore-music-video'          # per-project refcount for the shared override.cfg
START_RE = re.compile(r'MUSIC_VIDEO_SONG_START frame=(\d+) length=([0-9.]+)')
SHOT_RE = re.compile(r'MUSIC_VIDEO_SHOT (\d+) ([0-9.]+)-([0-9.]+) blocked=(\d+)%( CHECK)?')
ERROR_RE = re.compile(r'SCRIPT ERROR|Parse Error')
MOTION_RE = re.compile(r'lavfi\.signalstats\.YAVG=([0-9.]+)')
GPU_RESET_EVENTS = (4101, 4109)    # Display: driver stopped responding and recovered; application blocked from the GPU
GPU_RESET_EXIT = 3
GPU_RESET_QUERY = ("$b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime;"
                   "Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Display';StartTime=$b} -ErrorAction SilentlyContinue|"
                   "Where-Object {$_.Id -in " + ",".join(str(i) for i in GPU_RESET_EVENTS) + "}|"
                   "ForEach-Object {$_.TimeCreated.ToString('s')+' '+$_.Id}")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- vendor ----------
def vendor(project, dest=None, force=False, module='music-video'):
    """Install a GameCore Godot module into <project>/<dest> with a SHA-256 lock per file.
    Refuses to overwrite local edits unless forced."""
    spec = MODULES[module]
    dest = dest or spec['dest']
    project = Path(project)
    if not (project / 'project.godot').is_file():
        raise SystemExit(f'{project} is not a Godot project (no project.godot)')
    target_dir = project / dest
    lock_path = target_dir / spec['lock']
    if lock_path.exists() and not force:
        old = json.loads(lock_path.read_text(encoding='utf-8'))
        entries = old.get('files') or [{'name': RUNTIME.name, 'sha256': old.get('sha256')}]
        for entry in entries:
            installed = target_dir / entry['name']
            if installed.exists() and sha256(installed) != entry['sha256']:
                raise SystemExit(f'{installed} has local edits (digest differs from its lock); change GameCore instead or pass --force')
    target_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for rel in spec['files']:
        src = ROOT / rel
        target = target_dir / src.name
        shutil.copyfile(src, target)
        files.append({'name': src.name, 'source': 'ArcoreGameCore/' + rel, 'sha256': sha256(target),
                      'res_path': 'res://' + (Path(dest) / src.name).as_posix(), 'version': file_version(src)})
    lock = {'module': spec['id'], 'version': files[0]['version'], 'files': files,
            # The first file's digest and path at the top level: earlier single-file locks read these.
            'source': files[0]['source'], 'sha256': files[0]['sha256'], 'res_path': files[0]['res_path']}
    lock_path.write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8')
    return lock


def file_version(path):
    m = re.search(r'const (?:[A-Z_]*_)?VERSION := "([^"]+)"', Path(path).read_text(encoding='utf-8'))
    return m.group(1) if m else 'unknown'


def runtime_version():
    m = re.search(r'const VERSION := "([^"]+)"', RUNTIME.read_text(encoding='utf-8'))
    return m.group(1) if m else 'unknown'


# ---------- log parsing ----------
def parse_log(text):
    start = START_RE.search(text)
    shots = [{'index': int(m[1]), 'start': float(m[2]), 'end': float(m[3]), 'blocked_pct': int(m[4]), 'check': bool(m[5])} for m in SHOT_RE.finditer(text)]
    return {'start_frame': int(start[1]) if start else None, 'song_length': float(start[2]) if start else None,
            'finished': 'MUSIC_VIDEO_END' in text, 'shots': shots, 'checks': [s['index'] for s in shots if s['check']],
            'errors': [line for line in text.splitlines() if ERROR_RE.search(line)]}


# ---------- shared override.cfg (Movie Maker records at the window size) ----------
def override_text(width, height):
    return f'[display]\n\nwindow/size/window_width_override={width}\nwindow/size/window_height_override={height}\n'


def acquire_override(project, width, height):
    """Write a temporary override.cfg shared safely by parallel recordings of the same project.

    Returns a token for release_override. The first user saves any pre-existing override.cfg; the last user
    restores it (or removes ours). All users must request the same size.
    """
    project = Path(project)
    state = project / OVERRIDE_DIR
    state.mkdir(exist_ok=True)
    cfg = project / 'override.cfg'
    wanted = override_text(width, height)
    users = list(state.glob('user-*'))
    if not users:
        if cfg.exists():
            shutil.copyfile(cfg, state / 'preexisting.cfg')
        cfg.write_text(wanted, encoding='utf-8')
    elif cfg.read_text(encoding='utf-8') != wanted:
        raise SystemExit(f'Another recording of {project} is using a different window size; wait for it or use the same size')
    token = state / f'user-{os.getpid()}-{time.time_ns()}'
    token.write_text('', encoding='utf-8')
    return token


def release_override(token):
    token = Path(token)
    state = token.parent
    project = state.parent
    token.unlink(missing_ok=True)
    if list(state.glob('user-*')):
        return
    saved = state / 'preexisting.cfg'
    cfg = project / 'override.cfg'
    if saved.exists():
        shutil.copyfile(saved, cfg)
        saved.unlink()
    else:
        cfg.unlink(missing_ok=True)
    try:
        state.rmdir()
    except OSError:
        pass


# ---------- ffmpeg ----------
def probe_duration(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(path)], encoding='utf-8')
    return float(json.loads(out)['format']['duration'])


def mix_command(avi, song, out, offset, length, sfx_db=-4.0, fade=1.5, crf=20, title=''):
    end = length - fade
    filt = (f'[0:a]volume={sfx_db}dB,aresample=48000[sfx];[1:a]aresample=48000[song];'
            f'[song][sfx]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={end:.2f}:d={fade}[a];'
            f'[0:v]fade=t=out:st={end:.2f}:d={fade}[v]')
    cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', f'{offset:.3f}', '-t', f'{length:.3f}', '-i', str(avi), '-i', str(song),
           '-filter_complex', filt, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart']
    if title:
        cmd += ['-metadata', f'title={title}']
    return cmd + [str(out)]


def preview_bitrate(length, target_mb=28.0, audio_kbps=96):
    return max(200, int(target_mb * 8192 / length) - audio_kbps)


def preview_command(src, out, length, width=960, height=600, target_mb=28.0):
    v = preview_bitrate(length, target_mb)
    return ['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-vf', f'scale={width}:{height}', '-c:v', 'libx264', '-preset', 'slow',
            '-b:v', f'{v}k', '-maxrate', f'{int(v * 1.25)}k', '-bufsize', f'{v * 2}k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart', str(out)]


def sheet_command(src, out, every=13.0, columns=4, rows=5, width=480):
    return ['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-vf', f'fps=1/{every},scale={width}:-1,tile={columns}x{rows}', '-frames:v', '1', str(out)]


def godot_command(godot, project, script, song, fps=30, movie=None):
    cmd = [str(godot), '--path', str(project), '--fixed-fps', str(fps)]
    cmd += ['--write-movie', str(movie)] if movie else ['--headless']
    return cmd + ['--script', str(script), '--', f'--song={song}']


# ---------- GPU safety ----------
def gpu_resets_since_boot(run=subprocess.run, platform=os.name):
    """Display-driver reset events since the last boot, as 'ISO-time event-id' lines (Windows only; else [])."""
    if platform != 'nt':
        return []
    try:
        out = run(['powershell', '-NoProfile', '-NonInteractive', '-Command', GPU_RESET_QUERY], capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line.strip() for line in (out.stdout or '').splitlines() if line.strip()]


def gpu_preflight(a, check=gpu_resets_since_boot):
    """Refuse GPU work after a display-driver reset this boot (exit code 3), unless overridden."""
    if getattr(a, 'allow_after_gpu_reset', False):
        return
    events = check()
    if events:
        print(f'GPU_RESET_SINCE_BOOT {"; ".join(events)}', file=sys.stderr)
        print('The display driver reset since the last reboot. Reboot before recording, or pass --allow-after-gpu-reset.', file=sys.stderr)
        raise SystemExit(GPU_RESET_EXIT)


# ---------- commands ----------
def cmd_dry_run(a):
    log = Path(a.log or Path(tempfile.gettempdir()) / f'music-video-dry-{a.song}.log')
    with open(log, 'w', encoding='utf-8') as f:
        code = subprocess.run(godot_command(a.godot, a.project, a.script, a.song, a.fps), stdout=f, stderr=subprocess.STDOUT, timeout=a.timeout).returncode
    report = parse_log(log.read_text(encoding='utf-8', errors='replace'))
    report.update(song=a.song, exit_code=code, log=str(log))
    print(json.dumps({k: report[k] for k in ('song', 'exit_code', 'finished', 'song_length', 'checks', 'errors')} | {'shots': len(report['shots'])}))
    return 0 if report['finished'] and not report['errors'] else 1


def cmd_record(a):
    gpu_preflight(a)
    out_dir = Path(a.out);out_dir.mkdir(parents=True, exist_ok=True)
    width, height = (int(v) for v in a.resolution.lower().split('x'))
    avi = Path(a.avi_dir or tempfile.gettempdir()) / f'music-video-{a.song}-{os.getpid()}.avi'
    log = out_dir / f'{a.song}.record.log'
    token = acquire_override(a.project, width, height)
    try:
        with open(log, 'w', encoding='utf-8') as f:
            subprocess.run(godot_command(a.godot, a.project, a.script, a.song, a.fps, avi), stdout=f, stderr=subprocess.STDOUT, check=True, timeout=a.timeout)
    finally:
        release_override(token)
    report = parse_log(log.read_text(encoding='utf-8', errors='replace'))
    if report['start_frame'] is None or not report['finished']:
        raise SystemExit(f'Recorder did not finish; see {log}')
    length = probe_duration(a.audio) + a.tail
    out = out_dir / f'{a.song}-music-video.mp4'
    subprocess.run(mix_command(avi, a.audio, out, report['start_frame'] / a.fps, length, a.sfx_db, title=a.title or ''), check=True)
    if not a.keep_avi:
        avi.unlink(missing_ok=True)
    preview = out_dir / f'{a.song}-music-video-preview.mp4'
    subprocess.run(preview_command(out, preview, length, target_mb=a.preview_mb), check=True)
    sheet = out_dir / f'{a.song}-contact.png'
    subprocess.run(sheet_command(out, sheet, every=max(4.0, length / 20)), check=True)
    record = {'song': a.song, 'video': out.name, 'preview': preview.name, 'contact_sheet': sheet.name, 'duration': round(probe_duration(out), 3),
              'resolution': a.resolution, 'fps': a.fps, 'audio': str(a.audio), 'audio_sha256': sha256(a.audio), 'sfx_db': a.sfx_db,
              'trimmed_setup_s': round(report['start_frame'] / a.fps, 3), 'shots': len(report['shots']), 'blocked_checks': report['checks'],
              'recorder_log': log.name}
    (out_dir / f'{a.song}-music-video.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))
    return 0


def motion_command(video, start, end, fps=2):
    """Mean frame-to-frame luma difference over a shot (small, grey, 2 fps: cheap and stable)."""
    return ['ffmpeg', '-hide_banner', '-nostats', '-ss', f'{start:.2f}', '-to', f'{end:.2f}', '-i', str(video),
            '-vf', f'fps={fps},scale=320:-2,format=gray,tblend=all_mode=difference,signalstats,metadata=print:file=-',
            '-f', 'null', '-']


def parse_motion(text):
    values = [float(v) for v in MOTION_RE.findall(text)]
    return sum(values) / len(values) if values else 0.0


def dead_shots(shots, scores, threshold):
    """Shots whose picture barely changes: a still subject over an empty background."""
    return [s['index'] for s, score in zip(shots, scores) if score < threshold]


def cmd_motion(a):
    report = parse_log(Path(a.log).read_text(encoding='utf-8', errors='replace'))
    scores = []
    for s in report['shots']:
        run = subprocess.run(motion_command(a.video, s['start'], s['end']), capture_output=True, text=True)
        scores.append(round(parse_motion(run.stdout), 3))
    flagged = dead_shots(report['shots'], scores, a.threshold)
    result = {'video': str(a.video), 'threshold': a.threshold,
              'shots': [{'index': s['index'], 'start': s['start'], 'end': s['end'], 'motion': m} for s, m in zip(report['shots'], scores)],
              'dead_shots': flagged}
    print(json.dumps(result, indent=2))
    return 1 if flagged and a.strict else 0


SHOWCASE_RE = re.compile(r'SHOWCASE_SHOT ([A-Za-z0-9]+) ([0-9.]+)')


def tile_command(images, out, columns=4, width=640):
    """FFmpeg xstack: tile up to columns*2 images (scaled to one width) into one contact sheet."""
    n = len(images)
    cells = []
    for i in range(n):
        x = '+'.join(['w0'] * (i % columns)) or '0'
        y = 'h0' if i >= columns else '0'
        cells.append(f'{x}_{y}')
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    for img in images:
        args += ['-i', str(img)]
    chain = ''.join(f'[{i}]scale={width}:-2[s{i}];' for i in range(n)) + ''.join(f'[s{i}]' for i in range(n))
    if n == 1:
        return args + ['-vf', f'scale={width}:-2', str(out)]
    return args + ['-filter_complex', f'{chain}xstack=inputs={n}:layout={"|".join(cells)}:fill=black', str(out)]


def cmd_showcase(a):
    """Run an asset-showcase script windowed with --snap, then tile the PNGs into sheets of eight."""
    snaps = Path(a.out)
    snaps.mkdir(parents=True, exist_ok=True)
    log = snaps / 'showcase.log'
    if not a.sheets_only:
        gpu_preflight(a)
        cmd = [a.godot, '--path', str(Path(a.project).resolve()), '--fixed-fps', str(a.fps), '--script', str(Path(a.script).resolve()),
               '--', f'--song={a.song}', f'--snap={snaps.resolve()}'] + ([f'--only={a.only}'] if a.only else [])
        with open(log, 'w', encoding='utf-8') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=a.timeout)
    text = log.read_text(encoding='utf-8', errors='replace')
    ids = [m[1] for m in SHOWCASE_RE.finditer(text)]
    sheets = []
    for i in range(0, len(ids), 8):
        batch = [snaps / f'{x}.png' for x in ids[i:i + 8] if (snaps / f'{x}.png').exists()]
        if batch:
            out = snaps / f'sheet_{i // 8 + 1}.jpg'
            subprocess.run(tile_command(batch, out), check=True)
            sheets.append(out.name)
    result = {'shots': ids, 'sheets': sheets, 'errors': len(ERROR_RE.findall(text))}
    print(json.dumps(result))
    return 1 if result['errors'] else 0


def cmd_sheet(a):
    length = probe_duration(a.video)
    subprocess.run(sheet_command(a.video, a.out, every=max(4.0, length / 20)), check=True)
    print(a.out)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('vendor', help='copy the Godot recorder into a game project')
    v.add_argument('--project', required=True, help='Godot project folder (contains project.godot)')
    v.add_argument('--dest', help='install folder inside the project (default per module)')
    v.add_argument('--module', choices=sorted(MODULES), default='music-video', help='music-video (recorder + asset showcase) or world-life (kit)')
    v.add_argument('--force', action='store_true')
    for name in ('dry-run', 'record'):
        s = sub.add_parser(name)
        s.add_argument('--godot', default=os.environ.get('GODOT'), required=not os.environ.get('GODOT'), help='Godot 4 console executable (or $GODOT)')
        s.add_argument('--project', required=True)
        s.add_argument('--script', required=True, help="the game's recorder script (extends the vendored base)")
        s.add_argument('--song', required=True)
        s.add_argument('--fps', type=int, default=30)
        s.add_argument('--timeout', type=int, default=7200)
        if name == 'dry-run':
            s.add_argument('--log')
        else:
            s.add_argument('--audio', required=True, help='exact runtime song file mixed over the capture')
            s.add_argument('--out', required=True)
            s.add_argument('--resolution', default='1920x1200', help="window size Movie Maker records at; match the game's aspect")
            s.add_argument('--sfx-db', type=float, default=-4.0)
            s.add_argument('--tail', type=float, default=1.0, help='seconds after the song (fade-out)')
            s.add_argument('--preview-mb', type=float, default=28.0)
            s.add_argument('--title')
            s.add_argument('--avi-dir')
            s.add_argument('--keep-avi', action='store_true')
            s.add_argument('--allow-after-gpu-reset', action='store_true', help='record even though the display driver reset since the last boot')
    sh = sub.add_parser('sheet')
    sh.add_argument('video');sh.add_argument('out')
    sc = sub.add_parser('showcase', help='asset showcase: one PNG per shot (windowed, no movie) and contact sheets')
    sc.add_argument('--godot', default=os.environ.get('GODOT'), required=not os.environ.get('GODOT'))
    sc.add_argument('--project', required=True)
    sc.add_argument('--script', required=True)
    sc.add_argument('--out', required=True, help='folder for the PNGs, sheets and showcase.log')
    sc.add_argument('--song', default='showcase')
    sc.add_argument('--only', help='comma-separated shot-id first letters')
    sc.add_argument('--fps', type=int, default=30)
    sc.add_argument('--timeout', type=int, default=3600)
    sc.add_argument('--sheets-only', action='store_true', help='re-tile existing PNGs listed in the last showcase.log')
    sc.add_argument('--allow-after-gpu-reset', action='store_true', help='capture even though the display driver reset since the last boot')
    mo = sub.add_parser('motion', help='flag shots whose picture barely changes (empty backgrounds)')
    mo.add_argument('video');mo.add_argument('--log', required=True, help='recorder log with MUSIC_VIDEO_SHOT markers')
    mo.add_argument('--threshold', type=float, default=1.2, help='mean luma difference per frame below which a shot is dead')
    mo.add_argument('--strict', action='store_true', help='exit 1 when any shot is flagged')
    a = p.parse_args(argv)
    if a.command == 'vendor':
        print(json.dumps(vendor(a.project, a.dest, a.force, a.module)))
        return 0
    return {'dry-run': cmd_dry_run, 'record': cmd_record, 'sheet': cmd_sheet, 'motion': cmd_motion, 'showcase': cmd_showcase}[a.command](a)


if __name__ == '__main__':
    sys.exit(main())
