# VHS tape: two-command scaffold for the demo.
# 1. Install VHS: https://github.com/charmbracelet/vhs
# 2. Set WorkingDirectory to your Dev-Agent-System TEMPLATE clone (contains .agents/scripts/).
# 3. vhs demo.tape

Output demo.gif
Set Shell bash
Set FontSize 16
Set Width 1100
Set Height 520
Set Padding 24
Set Theme "Catppuccin Mocha"

# CHANGE THIS to your machine's path to the template repo root:
Set WorkingDirectory /path/to/Dev-Agent-System

Sleep 500ms
Type "python .agents/scripts/new-project.py --name PixelForge --description 'Pixel art editor for indie devs' --type 'Web App' --frontend 'React, TypeScript, Vite' --backend 'None' --output-dir /tmp/pixelforge-demo"
Sleep 200ms
Enter
Sleep 12s

Type "cd /tmp/pixelforge-demo && python .agents/scripts/new-feature.py --name pixel-editor --issue 1 --quiet"
Sleep 200ms
Enter
Sleep 10s

Sleep 1s
Type "ls -la .agents/updates/ | tail -n 5"
Sleep 200ms
Enter
Sleep 2s

Sleep 1s
