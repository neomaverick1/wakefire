"""The Generals' Barrow, on the Hill of Sleepers: Ushur and Baltu killed each other in the same
battle at the same moment, the city could not agree who had won, and so it buried them together,
with one door, and an army of clay apiece (counted, by both sides, twice).

  nod     board    truce
   .      pass2    red
  blue    pass1     .
   .      door      .

A passage grave. The door comes in from the hilltop at the foot of a long passage that runs
north into the mound. Off its first stretch, to the west, is Baltu's camp: his slingers across a
ditch, his standard behind them. Off its second, to the east, Ushur's: his spearmen and his.
Both standards down, and the head of the passage opens on the Board: the game of twenty
squares, floor-sized, and on its middle rosette the piece that has not moved in three hundred
and ninety-one years. It guards the quartermaster's pocket. West of the Board is the
quartermaster's post, and the quartermaster, asleep; east is the wall that has kept the two
armies apart since the funeral."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import kit
import town
import bprops
import dkit
from dkit import Floor, NW, DW, DH, PX
from forge import Model, M, m_brick, m_mottle

CELL = 40                                    # a square of the board, in pixels
BOARD = (48, 68)                             # its north-west corner, in the room
SQUARES = [(c, r) for r in range(3) for c in range(8) if r == 1 or c not in (4, 5)]
ROSETTES = [(0, 0), (0, 2), (3, 1), (6, 0), (6, 2)]


def wall(length, doors, sides):
    """A north wall of mud brick: a plastered band with shields hung along it (sides: which army's,
    in turn), a red line and a blue line under the coping."""
    m = Model()

    def near(x, margin):
        return any(abs(x - dx) < DW / 2 + margin for dx in doors)
    h, d = 2.75, 0.25
    foot = M('mud', 3.0, m_brick(8, 4))
    body = M('mud', 3.6, m_brick(8, 4))
    top = M('mud', 4.4, m_mottle(14, 0.4))
    m.part(); m.box(0, 0, 0, length, d, h, body, top=top)
    m.part(); m.box(0, -PX, 0, length, d, 0.5, foot, top=top)
    m.part(); m.box(0, -0.5 * PX, 0.98, length, d, 1.98, M('limewash', 3.2, m_mottle(12, 0.3)))
    m.part(); m.box(0, -PX, h - 0.5, length, d, h - 0.4, M('red', 3.1))
    m.part(); m.box(0, -PX, h - 0.38, length, d, h - 0.28, M('blue', 3.1))
    m.part(); m.box(0, -1.5 * PX, h - 0.14, length, d, h, M('mud', 4.2), top=top)
    x = 1.6; k = 0
    while x < length - 1.0:
        if not near(x, 0.75):
            bprops.wall_shield(m, x, 1.48, sides[k % len(sides)])
        x += 1.75; k += 1
    dark, trim = M('dark', 1.1), M('bronze', 4.0)
    for dx in doors:
        a, b = dx - DW / 2, dx + DW / 2
        m.part(); m.box(a - 0.25, -0.2, 0, b + 0.25, 0, DH + 0.3, foot, top=top)
        m.part(); m.quad((a, -0.21, 0), (b, -0.21, 0), (b, -0.21, DH), (a, -0.21, DH), dark)
        m.part(); m.box(a - 0.1, -0.24, DH, b + 0.1, -0.2, DH + 0.1, trim)
    return m


class Barrow(Floor):
    """A floor of the barrow: mud brick, packed earth, a herringbone walk."""

    def wall_model(self, rm, length, doors):
        return wall(length, doors, {'red': ['red'], 'blue': ['blue']}.get(rm.id, ['red', 'blue']))

    def floor_look(self, T, rm, sd, whole, fx, fy, fw, fh):
        H, W = self.H, self.W
        T.earth(whole, seed=sd, base=2.9, ramp='dust', pebbles=0.006)
        walk = T.rect(fx + 10, fy + 12, fw - 20, fh - 24)
        T.bricks(walk, seed=sd, bw=8, bh=4, ramp='tile', base=3.0, jitter=1.0, herring=True)
        T.border(walk, 'tile', 1.8, 1, 0.4)
        return True

    def tops_look(self, T, rm, sd, tops, gaps):
        T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=3.0, whole=False, crack=0.1)
        T.walltop(tops, seed=sd + 1, ramp='tile', base=3.3)
        return True

    def pillar(self, rm, x, y, kind=None):
        X, Y = rm.p(x, y)
        self.m.model("bw_pier", bprops.pier(), X, Y, box=(-8, -11, 8, 0), kind=kind)

    def partition(self, rm, x0, x1, y, h=1.2, layer=0):
        m = self.m
        m.set_into_ground(bprops.partition((x1 - x0) / 16.0, h=h), rm.ox + x0, rm.oy + y, seed=self.seed + x0 + y)
        m.solid(rm.ox + x0, rm.oy + y - int(h * 16) - 8, rm.ox + x1, rm.oy + y - 4)

    def partition_ns(self, rm, x, y0, y1, h=1.2, layer=0):
        m = self.m
        if y0 > NW + 4:
            m.model(f"bw_wall_ns_{y1 - y0}_{int(h * 10)}", bprops.partition_ns((y1 - y0) / 16.0, h=h), rm.ox + x, rm.oy + y1, box=None)
        else:
            m.set_into_ground(bprops.partition_ns((y1 - y0) / 16.0, h=h), rm.ox + x, rm.oy + y1, seed=self.seed + x)
        m.solid(rm.ox + x, rm.oy + y0, rm.ox + x + 8, rm.oy + y1, layer)

    def board(self, rm):
        """The game of twenty squares, set into a room's floor (before the bake): pale squares edged in
        lapis, five of them rosettes."""
        T = self.T
        H, W = self.H, self.W
        ox, oy = rm.ox + BOARD[0], rm.oy + BOARD[1]
        xx, yy = T.xx, T.yy
        for (c, r) in SQUARES:
            x0, y0 = ox + c * CELL, oy + r * CELL
            sq = T.rect(x0, y0, CELL, CELL)
            inner = T.rect(x0 + 2, y0 + 2, CELL - 4, CELL - 4)
            T.put(sq, 'lapis', np.full((H, W), 2.2), 0.6)
            cx, cy = x0 + CELL / 2 - 0.5, y0 + CELL / 2 - 0.5
            dx, dy = xx - cx, yy - cy
            rr = np.hypot(dx, dy)
            if (c, r) in ROSETTES:
                T.put(inner, 'lapis', np.full((H, W), 3.0) + ((xx + yy) % 5 == 0) * 0.5, 1.0)
                th = np.arctan2(dy, dx)
                petal = inner & (rr < 15.5 * (0.45 + 0.55 * np.abs(np.cos(4 * th)))) & (rr > 3.5)
                T.put(petal, 'gold', np.full((H, W), 3.4) + (rr > 11) * 0.8, 1.6)
                T.put(inner & (rr <= 3.5), 'carpet', np.full((H, W), 3.6), 1.8)
                ring = inner & (np.abs(rr - 17.0) < 0.8)
                T.put(ring, 'gold', np.full((H, W), 2.6), 1.2)
            else:
                T.put(inner, 'pale', np.full((H, W), 3.3) + (T_hash(xx, yy, c, r) - 0.5) * 0.7, 1.0)
                if (c + r) % 2 == 0:
                    # five eyes, the way the old boards have them
                    for (ex, ey) in ((-10, -10), (10, -10), (0, 0), (-10, 10), (10, 10)):
                        e = np.hypot(dx - ex, dy - ey)
                        T.put(inner & (e < 3.6), 'lapis', np.full((H, W), 3.6), 1.3)
                        T.put(inner & (e < 1.5), 'pale', np.full((H, W), 5.0), 1.5)
                else:
                    # a field of small dots
                    dot = inner & (((xx - x0) % 8 == 4) & ((yy - y0) % 8 == 4))
                    T.put(dot, 'carpet', np.full((H, W), 3.0), 1.2)
        self.m.marker("board", ox, oy, w=CELL, h=CELL)


def T_hash(xx, yy, c, r):
    from forge import hash2
    return hash2(xx // 5 + c * 31, yy // 5 + r * 17, 7)


def cage(F, rm, x, y, uid, when, w=4.5, say=None):
    """An alcove against the north wall with a grille across its mouth."""
    half = int(w * 8)
    F.partition_ns(rm, x - half - 8, 48, y - 4)
    F.partition_ns(rm, x + half, 48, y - 4)
    F.bars(rm, x, y, uid, when, w=w, say=say)


def barrow():
    F = Barrow("barrow", 3, 4, 'barrow', dungeon='barrow', label='B1', order=1, music='barrow', seed=171)
    door = F.room("door", 1, 3, name="The One Door", opts="dim")
    pass1 = F.room("pass1", 1, 2, name="The Long Passage", opts="dim")
    blue = F.room("blue", 0, 2, name="The Blue Camp", opts="dim")
    pass2 = F.room("pass2", 1, 1, name="The Head of the Passage", opts="dim")
    red = F.room("red", 2, 1, name="The Red Camp", opts="dim")
    board = F.room("board", 1, 0, name="The Board", opts="dim")
    nod = F.room("nod", 0, 0, name="Nod's Post", opts="dim")
    truce = F.room("truce", 2, 0, name="The Truce Wall", opts="dim")
    board.mark = "mini"
    F.link(1, 3, 's', 'out', to="necropolis", spawn="barrow", name="south")
    F.link(1, 3, 'n')
    F.link(1, 2, 'w')
    F.link(1, 2, 'n')
    F.link(1, 1, 'e', 'bars', id="bw_reddoor", when="clear:red", opts="shut:red")
    F.link(1, 1, 'n', 'bars', id="bw_board", when="flag:bw_red;flag:bw_blue",
           say="Both standards are down. At the head of the passage, bronze bars lift.^Up on the hill, two old men stop arguing for the first time in four centuries.| It does not last.",
           far={"id": "bw_shut", "when": "clear:board", "opts": "shut:board"})
    F.link(1, 0, 'w', 'bars', id="bw_west", when="flag:dead_bw_piece")
    F.link(1, 0, 'e', 'bars', id="bw_east", when="flag:dead_bw_piece")
    # no two rooms the same shape: an eight-sided hall, two arms of a passage, camps with their corners built up, an L
    F.corners(door, 32)
    F.passage(pass1, 'ns', 96, stubs='w')
    F.passage(pass2, 'ns', 96, stubs='e')
    F.corners(blue, 32)
    F.corners(red, 32)
    F.shape(nod, [(16, 48, 400, 132), (168, 132, 400, 208)])
    F.lay()
    F.board(board)
    F.bake()
    m = F.m

    # ---------------------------------------------------------------- the one door
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(door, x, y)
    F.torch(door, 44, 84); F.torch(door, 372, 84)
    F.plaque(door, 110, "{g}'HERE LIE USHUR AND BALTU, WHO KILLED EACH OTHER IN THE SAME BATTLE AT THE SAME MOMENT.'{/}^"
                        "{g}'THE CITY COULD NOT AGREE WHO HAD WON, AND BURIED THEM TOGETHER.'{/}^"
                        "Underneath, in two hands: {g}'I WON.'{/}| {g}'HE DID NOT.'{/}")
    F.plaque(door, 306, "{g}'EACH GENERAL TOOK AN ARMY OF CLAY INTO THE DARK. THEY WERE COUNTED, BY BOTH SIDES, TWICE.'{/}^"
                        "{g}'THE WAY NORTH OPENS WHEN BOTH STANDARDS ARE DOWN. NEITHER WILL TAKE HIS DOWN FIRST.'{/}^"
                        "Scratched below, by a mason: {g}'this is why we could not have two doors.'{/}")
    F.chest(door, 340, 186, "bw_map", "map_barrow")
    X, Y = door.p(66, 200); m.model("drum_blue", bprops.drum('blue'), X, Y, box=(-6, -8, 6, 0))
    X, Y = door.p(350, 200); m.model("drum_red", bprops.drum('red'), X, Y, box=(-6, -8, 6, 0))
    for (x, y) in ((88, 204), (346, 120), (60, 120)):
        kit.pot(m, *door.p(x, y))
    F.dreamthing(door, 262, 96, "bw_word", "word", "dream_word", bprops.last_word(), source=True)
    for k, (x, y) in enumerate(((150, 150), (270, 140))):
        F.enemy(door, "scarab", x, y, f"bw_s{k}")

    # ---------------------------------------------------------------- the passage: two stretches, a camp off each
    F.torch(pass1, 60, 108); F.torch(pass1, 246, 196)
    F.look("stele_bw", town.stele(1.25, 1), pass1, 240, 76, (-5, -5, 5, 0),
           "{g}'WEST: THE CAMP OF BALTU. HE WILL TELL YOU IT IS THE LARGER.'{/}^{g}'FURTHER IN, EAST: THE CAMP OF USHUR. HE WILL TELL YOU THE SAME.'{/}| "
           "Both camps are exactly the same size. The masons measured. They were made to.")
    for k, (x, y) in enumerate(((208, 92), (208, 170))):
        F.enemy(pass1, "scarab", x, y, f"bw_s{k + 2}")
    for (x, y) in ((172, 198), (30, 150)):
        kit.pot(m, *pass1.p(x, y))
    F.torch(pass2, 356, 108); F.torch(pass2, 170, 196)
    F.look("stele_bw", town.stele(1.25, 1), pass2, 176, 76, (-5, -5, 5, 0),
           "{g}'THE BOARD. NO SPEARS, NO SLINGS, NO ADVICE FROM THE GALLERY.'{/}^{g}'A STANDARD THAT IS FLYING IS A GENERAL WHO IS STILL PLAYING.'{/}^"
           "{g}'RULE THE FOURTH: A PIECE THAT STANDS ON A ROSETTE CANNOT BE TAKEN.'{/}| Somebody has underlined the fourth rule. Twice, in two different hands.")
    for k, (x, y) in enumerate(((244, 190), (380, 150))):
        kit.bones(m, *pass2.p(x, y), k)
    kit.pot(m, *pass2.p(244, 70))

    # ---------------------------------------------------------------- the red camp: spearmen, and the standard behind them
    cage(F, red, 208, 108, "bw_redcage", "clear:red", say="The last of Ushur's spearmen goes to pieces.^The grille in front of his standard lifts. Nobody is left to mind.")
    F.standard(red, 208, 90, 'red', "bw_red")
    for k, (x, y) in enumerate(((128, 150), (208, 164), (288, 150))):
        F.enemy(red, "clay_red", x, y, f"bw_r{k}", once=True)
    X, Y = red.p(80, NW); m.model("rack_red", bprops.shield_rack('red'), X, Y + 6, box=(-13, -5, 13, 0))
    X, Y = red.p(336, NW); m.model("rack_red", bprops.shield_rack('red'), X, Y + 6, box=(-13, -5, 13, 0))
    X, Y = red.p(60, 190); m.model("drum_red", bprops.drum('red'), X, Y, box=(-6, -8, 6, 0))
    F.torch(red, 44, 84); F.torch(red, 372, 84)
    F.brazier(red, 120, 106, lit=True); F.brazier(red, 296, 106, lit=True)
    F.plaque(red, 306, "{g}'USHUR'S THIRD FOOT. MOTTO: FORWARD.'{/}^Underneath: {g}'THERE WAS A SECOND MOTTO. IT WAS ALSO FORWARD.'{/}")
    F.dreamthing(red, 340, 190, "bw_planks", "plank", "dream_planks", bprops.plank_stack(), box=(-11, -6, 11, 0), source=True)
    for (x, y) in ((60, 66), (76, 62), (292, 204)):
        kit.pot(m, *red.p(x, y))

    # ---------------------------------------------------------------- the blue camp: slingers across a ditch
    F.pit(blue, 16, 108, 192, 132, seed=7)
    F.pit(blue, 224, 108, 400, 132, seed=8)
    F.bars(blue, 208, 134, "bw_bluegate", "clear:blue", w=2.0,
           say="The last of Baltu's slingers goes to pieces.^The grille across the ditch lifts.")
    F.standard(blue, 208, 70, 'blue', "bw_blue")
    for k, (x, y) in enumerate(((96, 94), (320, 94), (150, 86))):
        F.enemy(blue, "clay_blue", x, y, f"bw_b{k}", once=True)
    # their watch fires, so a man across the ditch can see what is throwing at him
    F.brazier(blue, 64, 80, lit=True); F.brazier(blue, 352, 80, lit=True)
    F.look("stele_bw", town.stele(1.25, 1), blue, 336, 192, (-5, -5, 5, 0),
           "{g}'BALTU'S SLINGERS. MOTTO: FROM OVER THERE.'{/}^Underneath: {g}'A SLINGER FEARS TWO THINGS: A POLISHED SHIELD, AND HIS OWN AIM.'{/}")
    X, Y = blue.p(60, 184)
    m.model("tripod", bprops.tripod(), X, Y, box=(-6, -8, 6, 0), kind="look",
            data={"id": "say", "text": "A bronze bowl on three legs, cold. The ash in it is older than the city wall.~~"
                                       "In the dream somebody has kept the fire in.^It burns blue, and the heat of it goes the wrong way: into the fire, not out."})
    F.dreamthing(blue, 60, 185, "bw_fire", "flame", "dream_fire", lambda fi: bprops.tripod(True, fi), box=(-6, -8, 6, 0), source=True, frames=4)
    X, Y = blue.p(348, 200); m.model("rack_blue", bprops.shield_rack('blue'), X, Y, box=(-13, -5, 13, 0))
    F.torch(blue, 44, 140); F.torch(blue, 150, 198); F.torch(blue, 276, 198)

    # ---------------------------------------------------------------- the board
    bx, by = BOARD
    # the pocket, in the gap the board leaves in its top row
    gx = bx + 5 * CELL
    F.partition_ns(board, gx - 44, 48, 104)
    F.partition_ns(board, gx + 36, 48, 104)
    F.bars(board, gx, 108, "bw_cage", "flag:dead_bw_piece", w=4.5)
    F.bigchest(board, gx, 92, "bw_pocket", "pocket")
    F.plaque(board, 110, "{g}'THE GAME OF TWENTY SQUARES. RULE THE FOURTH: A PIECE THAT STANDS ON A ROSETTE CANNOT BE TAKEN.'{/}^"
                         "Under it, in two hands: {g}'YES IT CAN.'{/}| {g}'NO IT CANNOT.'{/}| {g}'LOOK IT UP.'{/}")
    m.marker("enemy", board.ox + bx + 3 * CELL + CELL // 2, board.oy + by + CELL + CELL // 2 + 4, who="last_piece", id="bw_piece", text="once")
    F.torch(board, 28, 84); F.torch(board, 388, 196); F.torch(board, 28, 196)

    # ---------------------------------------------------------------- Nod's post
    F.look("nod_bench", bprops.nod_bench(), nod, 110, 88, (-18, -11, 18, 0),
           "A sentry of clay, lying down. Every other soldier in the barrow was made standing up.^The potter had clearly met him.| "
           "He has his helmet over his eyes and his shield for a pillow, and he has not been disturbed since the funeral.~~"
           "In the dream the bench is exactly the same.^Nod is the one soldier here who looks the same asleep as awake. He practised.")
    X, Y = nod.p(196, NW)
    m.model("hook", bprops.hook(), X, Y + 1, box=None, shadow=False)
    F.dreamthing(nod, 196, 0, "bw_key", "key", "dream_key", bprops.dream_key(), box=(-7, -4, 7, 0), wall=True)
    F.dreamthing(nod, 146, 94, "bw_snore", "snore", "dream_snore", lambda fi: bprops.snore(fi), source=True, frames=4)
    F.plaque(nod, 250, "{g}'NOD. QUARTERMASTER TO BOTH ARMIES, WHICH NEITHER GENERAL KNEW.'{/}^"
                       "{g}'HE WAS THE BEST WE EVER HAD. HE WAS ALWAYS FINDING USEFUL THINGS IN HIS DREAMS.'{/}^"
                       "{g}'THE ONLY PROBLEM WAS, WE ALWAYS CAUGHT HIM SLEEPING ON THE JOB.'{/}| It is the second thing they ever agreed on.")
    # the strongroom: what he kept, and a lock he kept the key to in his sleep
    F.partition_ns(nod, 300, 48, 104)
    F.dreamlock(nod, 354, 108, "bw_strong", w=5.75)
    F.chest(nod, 354, 90, "bw_pay", "shekels:100")
    for (x, y) in ((322, 66), (386, 64)):
        kit.pot(m, *nod.p(x, y))
    F.torch(nod, 44, 122); F.torch(nod, 372, 196); F.torch(nod, 186, 196)
    for (x, y) in ((40, 70), (56, 66), (220, 200)):
        kit.pot(m, *nod.p(x, y))

    # ---------------------------------------------------------------- the truce wall
    # his side of the room: a prize behind a grille, a drop, and a cold lamp on the far side of it
    F.pit(truce, 16, 156, 152, 188, seed=9, planks=[(72, 96)])
    F.partition_ns(truce, 150, 48, 208)
    F.bars(truce, 83, 96, "bw_prize", "clear:truce", w=8.25,
           say="It is over. It took three hundred and ninety-one years, and about nine seconds.^In the corner, a grille lifts.")
    F.chest(truce, 83, 72, "bw_vessel", "vessel")
    F.plank(truce, 84, 156, 188, "bw_plank")
    F.bluelamp(truce, 84, 205, "bw_lamp")
    # the parade ground: red to the north, blue to the south, and the grille that has kept them apart
    F.partition(truce, 158, 200, 136, h=1.0)
    F.partition(truce, 360, 400, 136, h=1.0)
    F.bars(truce, 280, 134, "bw_truce", "lit:bw_lamp", w=10.0,
           say="The lamp that means the truce is over.^Along the wall, bronze lifts.| The truce held for three hundred and ninety-one years. It turns out it was the gate.")
    for k, (x, y) in enumerate(((230, 84), (330, 84))):
        m.marker("enemy", truce.ox + x, truce.oy + y, who="clay_red", id=f"bw_tr{k}", text="hold:on_bw_lamp")
    for k, (x, y) in enumerate(((230, 184), (330, 184))):
        m.marker("enemy", truce.ox + x, truce.oy + y, who="clay_blue", id=f"bw_tb{k}", text="hold:on_bw_lamp")
    F.look("stele_bw", town.stele(1.25, 1), truce, 124, 130, (-5, -5, 5, 0),
           "{g}'THE TRUCE OF THE BARROW. NEITHER ARMY SHALL CROSS THE WALL WHILE THE LAMP IS COLD.'{/}^"
           "{g}'THE LAMP TAKES NO FIRE OF THIS WORLD. WE ARE NOT FOOLS.'{/}| Somebody has scratched under it: {g}'SPEAK FOR YOURSELF.'{/}")
    F.torch(truce, 30, 110); F.torch(truce, 386, 60); F.torch(truce, 386, 200)
    X, Y = truce.p(180, NW); m.model("rack_red", bprops.shield_rack('red'), X, Y + 6, box=(-13, -5, 13, 0))
    X, Y = truce.p(380, 204); m.model("drum_blue", bprops.drum('blue'), X, Y, box=(-6, -8, 6, 0))
    F.save()


if __name__ == "__main__":
    barrow()
