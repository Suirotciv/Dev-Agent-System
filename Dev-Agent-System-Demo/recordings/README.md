# Terminal recordings for the demo

Goal: show the **real** bootstrap + feature scaffold in a terminal, so “one command” is believable before you cut to agent artifacts.

## Option A — asciinema (quick)

1. Install: [asciinema.org/docs/installation](https://asciinema.org/docs/installation)
2. From the **Dev-Agent-System template repo root** (the one that contains `.agents/scripts/`):

```bash
asciinema rec pixelforge-bootstrap.cast
```

3. In the recording shell, run the two commands from [`../DEMO.md`](../DEMO.md) Act 1 (`bootstrap.py`, then `new-feature.py`).  
   For `bootstrap`, use answers that match your story (e.g. project name **PixelForge**).
4. `exit` to stop. Upload: `asciinema upload pixelforge-bootstrap.cast` or embed locally.

**Non-interactive alternative** (clean single take, no wizard):

```bash
asciinema rec pixelforge-scaffold.cast
python .agents/scripts/new-project.py \
  --name "PixelForge" \
  --description "Pixel art editor for indie devs" \
  --type "Web App" \
  --frontend "React, TypeScript, Vite" \
  --backend "None" \
  --output-dir /tmp/pixelforge-demo
cd /tmp/pixelforge-demo
python .agents/scripts/new-feature.py --name pixel-editor --issue 1 --quiet
exit
```

Same architecture as Day 0 + Day 1; easier to automate and re-record.

## Option B — VHS (GIF / MP4)

1. Install: [github.com/charmbracelet/vhs](https://github.com/charmbracelet/vhs)
2. Edit `demo.tape`: set `WorkingDirectory` to **your** Dev-Agent-System template clone path (or use WSL paths if you record from Linux).
3. Run:

```bash
vhs demo.tape
```

4. Commit or attach the generated `demo.gif` (or change `Output` in the tape to `.mp4`).

## Helper script

`run-noninteractive-demo.sh` runs the two-step scaffold into `/tmp` for a repeatable take (bash + Python on PATH).
