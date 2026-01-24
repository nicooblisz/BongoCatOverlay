# BongoCatOverlay
I vibecoded Bongo Cat for Mac because I need the emotional support quick and can't invest time to learn objective C and Cocoa. 

**UPDATE:**
I let ChatGPT code a python version (BongoCat.py) of the script and now it runs on more OS's.

#### Credits
Images from https://github.com/Externalizable/bongo.cat.git

#### Usage
  1. Start with Terminal: ```$ path/to/BongoCat```
  2. Drag to a position you like.
  3. Click circular menubar icon.
  4. Toggle Click-Through.
  5. Smash your keyboard.

#### Requirements (Python Version)
``pip install PyQt5 keyboard``

#### Known Issues
  - MacOS probably stops the execution due to security concerns. You can run it anyway under "Settings" -> "Privacy & Security". Scroll down until a message about BongoCat appears.
  - Your "Terminal" Application needs access to Accessability functions to read your keyboard. You'll find it also under "Privacy & Security".


#### ToDo
- [ ] Tracking stats
- [ ] Implementing random chance for special events
- [ ] Currently it cycles 3 idle frames, I planned to animate but i will scrap that and display one idle frame
- [ ] Dragging is crappy
- [ ] Image manipulation would be nice (eg. rotating the cat)
- [x] Windows Implementation (somewhat done with python version)
- [ ] Display Cat from seperate files, currently every frame is a complete image
