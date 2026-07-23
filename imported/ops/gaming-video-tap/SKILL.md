---
name: gaming-video-tap
description: "Tap into, capture, monitor, and control video feeds and virtual displays in headless game streaming setups (Sunshine + Steam on NVIDIA datacenter GPUs like V100 in Docker). Supports screenshot/video capture of the X11 desktop, window inspection/control via xdotool/wmctrl, restarting services, sending inputs, and basic stream quality checks. Use when debugging why Steam UI isn't showing, Sunshine capture issues, or needing to interact with the virtual desktop remotely."
tags: [gaming, sunshine, steam, headless, v100, video, capture, x11, control, streaming, docker]
platforms: [linux]
---

# Gaming Video Tap & Control Skill

## Purpose
Enable direct interaction with the "video feeds" (the virtual X11 desktop rendered by Xorg inside the container, captured by Sunshine for streaming to Moonlight clients, and viewable via noVNC).

This includes:
- Capturing current desktop state (screenshots or short video clips).
- Inspecting/controlling windows (bring Steam Big Picture to front, click, type).
- Monitoring and restarting related services (Xorg, desktop, steam, sunshine).
- Tapping Sunshine's local output or the X display for debugging crashes, black screens, or UI not launching.
- Controlling the feed (e.g., force focus, simulate user input if the UI is stuck on login or options).

## When to Use
- Steam client starts (processes visible) but UI not in foreground or not visible on noVNC/Sunshine.
- Sunshine restarts or capture fails (exit 11, etc.).
- Need to "see" what's on the virtual desktop without physical monitor.
- Debug CEF/webhelper issues, bigpicture not showing, steambghelper prompts.
- User grants permission to tap/control the feeds (as in this session).

## Core Commands & Patterns (run via docker exec on the container, e.g. v100-steam)

### Capture Current Video Feed (Desktop)
```bash
# Ensure tools
docker exec <container> apt-get update && docker exec <container> apt-get install -y x11-apps imagemagick wmctrl xdotool 2>/dev/null || true

# Screenshot the root window (the full virtual desktop feed)
docker exec <container> sh -c 'DISPLAY=:0 xwd -root | convert xwd:- png:/tmp/desktop-$(date +%s).png && ls -l /tmp/desktop-*.png'

# Copy to host for analysis (read_file supports images)
docker cp <container>:/tmp/desktop-*.png /home/nick/tmp/

# Short video clip of the feed (e.g. 5s at 10fps for debugging)
docker exec <container> sh -c 'DISPLAY=:0 ffmpeg -f x11grab -video_size 1600x900 -framerate 10 -i :0 -t 5 -y /tmp/feed-clip.mp4 2>/dev/null && ls -l /tmp/feed-clip.mp4'
docker cp <container>:/tmp/feed-clip.mp4 /home/nick/tmp/
```

### Inspect & Control Windows / Feed
```bash
# List windows (see if Steam Big Picture or desktop is there)
docker exec <container> sh -c 'DISPLAY=:0 wmctrl -l || xwininfo -root -tree | head -30'

# Get active window name
docker exec <container> sh -c 'DISPLAY=:0 xdotool getactivewindow getwindowname'

# Bring Steam to front / focus Big Picture
docker exec <container> sh -c 'DISPLAY=:0 xdotool search --name "Steam" windowactivate || xdotool search --class Steam windowactivate'

# Simulate input if needed (e.g. to dismiss dialogs, login, or launch a game)
docker exec <container> sh -c 'DISPLAY=:0 xdotool key --clearmodifiers Return'
docker exec <container> sh -c 'DISPLAY=:0 xdotool mousemove 800 450 click 1'  # center click example
```

### Control Services (restart feeds)
```bash
docker exec <container> supervisorctl status
docker exec <container> supervisorctl restart xorg desktop steam sunshine x11vnc
# Or individually: supervisorctl start steam
```

### Tap Sunshine Stream Locally (if needed for quality/debug)
Sunshine listens on the container's ports. For internal capture:
- Use the noVNC port (usually mapped) or query Sunshine API if enabled.
- For direct: ffmpeg can capture the X11 as above (that's the source feed before Sunshine encodes it).

## Usage in This Session
- Capture the current desktop to see why Steam "isn't loading in the foreground".
- If only desktop/XFCE is visible (no Big Picture), use window control to activate Steam or restart the steam supervisor entry.
- If black screen or crash, capture multiple frames, check logs, restart services.
- Build on the existing headless-game-streaming skill.

## Integration
- Works with the `headless-game-streaming` skill (use its container name, references to xorg.conf, etc.).
- For video PoC or demos, combine with bbp-video-poc patterns (record the feed clip + narration).
- Host-side: if using noVNC or Moonlight, the captured feed inside is the authoritative "what the client sees" source.

## Limitations & Safety
- Only on the virtual :0 inside the privileged gaming container.
- X must be up (check with supervisor or xwininfo).
- Input simulation can interfere with active streams — use sparingly and only with permission.
- Large captures: limit resolution/framerate.
- Always clean /tmp/*.png /tmp/*.mp4 after use.

## References
- See /home/nick/.hermes/skills/gaming/headless-game-streaming/SKILL.md and references/ for container setup.
- V100-specific: nvidia-drm modeset, dummy X config, driver injection in container.
- Tools used: xwd, convert (ImageMagick), xdotool, wmctrl, ffmpeg (x11grab), supervisorctl, docker cp/exec.

This skill gives full read/write access to the video feeds as granted.
