# WAKEFIRE

![WAKEFIRE](docs/showcase.jpg)

**Chapter One: The Sleeping God.** A top-down action-adventure in 32-bit pixel art, built in Unity 6 for Android, iPhone and the web.

Forty nights ago Ninhal, god of the sky, lay down on top of his ziggurat for a nap. The whole bronze-age city of Ashkel fell asleep with him: bakers, priests, soldiers, babies and dogs. The only one still awake is Azar, the night watchman. He carries a bronze khopesh and the Wakefire, an old lantern that never goes out.

When Azar nods off, the world flips. A ring of gold sweeps out from where he stands, and inside it is the dream version of the same street. Walls are missing there, bridges of moonlight cross the sea, and every sleeper's dream-self is up and talking. The problem is that Azar can't stay asleep for long.

**Play it:** [in your browser](https://neomaverick1.github.io/wakefire) · [Android APK and iPhone project](https://github.com/neomaverick1/wakefire/releases/latest)

## Screens

| | |
|---|---|
| ![The Temple Gate square](docs/screens/01-gate-square.png) | ![Nodding off](docs/screens/02-nodding-off.png) |
| The Temple Gate square: Captain Dur asleep on his feet, the Wakefire catching a brazier | Nodding off: the ring of the dream sweeps across the square |
| ![The goat](docs/screens/03-the-goat.png) | ![Dur, age six](docs/screens/04-dur-age-six.png) |
| The goat is awake. The goat has always been awake. | In the dream, the captain is six years old and afraid of the dark |
| ![The lower town](docs/screens/05-lower-town.png) | ![The road of moonlight](docs/screens/06-road-of-moonlight.png) |
| The lower town: every sleeper's dream-self has something to say | A road of moonlight over the sea, only there while you dream |
| ![The temple yard](docs/screens/07-temple-yard.png) | ![The Brazen Bull](docs/screens/08-brazen-bull.png) |
| The long road across the chasm, for someone who can dream long enough | The summit: the Brazen Bull, the high priest's guilt cast in bronze, breathing fire at the Mirror Shield |

## The chapter

- **The Temple Gate square.** Captain Dur sleeps standing up with the gate key on his belt, and he won't let go of it. His dream-self is a six-year-old boy who is afraid of the dark. Light three braziers with the Wakefire and he'll hand the key over.
- **Lower Ashkel.** Hesha the baker kneads dough that isn't there. Kesh the potter sells sacred vessels for very sacred prices. The oracle Ummi prophesies in her sleep, mostly about snacks. There is also a tax collector asleep in the road, a boy guarding flour from a goat, and a young man who has been serenading a sleeping woman for forty nights.
- **The sea cliffs.** Brine crabs have stolen Abu-Nur's Night Oil. Get it back and your dreams last twice as long.
- **The olive terraces.** Jackals hunt in pairs. An old shrine keeps something for anyone who looks twice.
- **The temple yard.** A chasm with a long road of moonlight across it, for someone who can dream long enough.
- **The ziggurat.** Walls that exist in only one world, blocks to shove, bronze sentinels, a bull's head that breathes fire, the Bronze Mirror Shield, and at the summit, open to the storm, the reason the god won't wake up.

And the goat. The goat is everywhere.

## Controls

| | Keyboard | Gamepad | Touch |
|---|---|---|---|
| Move | WASD / arrows | Left stick / d-pad | Thumb down anywhere on the left |
| Khopesh (3-hit combo) | J / Space | X / Square | Blade button |
| Roll | K / Shift | B / Circle | Roll button |
| Talk, look, open | E / Enter | A / Cross | Speech button |
| Hold out the Wakefire | F / I | RB / R1 | Lamp button |
| Nod off / wake up | Q / L | Y / Triangle | Moon button |
| Pause | Esc / P | Start | Pause button |

The game saves every time you walk into a new place and every time you find something. On phones the controls stay clear of notches and rounded corners.

## How it's made

- **Unity 6 (URP)**, with everything in the game built from code at startup. The scene file is empty.
- **The pixel look** comes from a 216-line render target at 16 pixels per tile. The camera snaps to whole pixels and slides the finished image by sub-pixel amounts, so scrolling stays smooth. A separate light layer (moonlight plus torchlight) is multiplied over the picture, and the dream is repainted per pixel by the same shader that draws the gold ring.
- **Azar** is drawn the way 16-bit sprites were: every pixel of his front, side and back placed by hand on a grid (`Art/pixel/azar_v3.txt`), then animated from those key poses, a foot lifted, a body bob, lids lowered, the crest flickering, the khopesh and its swing drawn over the top (`Art/pixel/azar.py`). **The rest of the cast** is built the same way part by part: hand-placed faces and headwear, bodies and props with a dark outline round each part (`Art/pixel/folk.py`, `beasts.py`). The Brazen Bull and the sleeping god are modelled as lit solids in a tiny depth buffer, so masses that meet blend into one bronze casting, then cut down to a short palette with no anti-aliasing (`Art/pixel/bull.py`, `god.py`). The gate guardians were modelled in Blender in pixel units (`Art/blender`).
- **Places and props** are drawn by small Python programs pixel by pixel: lawns with tufts and flower patches, trodden earth, beach sand, limestone cliffs, olive trees and bushes built from lit clumps, glazed brick and bevelled clay floors, all from hue-shifted ramps with hand-placed details (`Art/pixel`).
- **The text face** is hand-set in a 7-pixel grid (`Art/pixel/font.py`). Every character speaks in their own synthesized voice.
- **The score** is written note by note in the Hijaz mode and played on a General MIDI soundfont (`Art/audio/music.py`). Every place has a waking arrangement and a dream arrangement of the same notes at the same length, so nodding off crossfades the music in the middle of a phrase. The sound effects and night ambience are synthesized from scratch (`Art/audio/sfx.py`, `Art/audio/ambience.py`).

## Building

Open the project in Unity 6000.6.9f1 with the Android, iOS and Web modules installed, or build from the command line:

```
Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Builder.Android      # Builds/Android/Wakefire.apk
Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Builder.AndroidBundle
Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Builder.IOS          # Xcode project in Builds/iOS
Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Builder.Web
```

The asset generators need Python 3 with numpy, scipy, Pillow, `bpy` (Blender as a module) and `tinysoundfont`, plus ffmpeg. To regenerate the music, place `GeneralUser-GS.sf2` in `Art/audio/`.

## Credits

Made by **Randy Kundinger**.

The logo uses Cinzel by Natanael Gama (SIL Open Font License). The music is played on GeneralUser GS by S. Christian Collins.

© 2026 Randy Kundinger. All rights reserved.
