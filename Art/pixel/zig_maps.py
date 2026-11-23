"""Inside the ziggurat of Ninhal: three floors of rooms under the summit where the god sleeps.

1F  the first hall and what opens off it: a block and a plate, a wall the dream does not have,
    a locked door, a chasm only moonlight crosses, and a vault that waits for the mirror shield.
2F  the Mirror Shield, and the bulls' heads that teach what it is for.
3F  the Bronze Herdsman and his sling, the Bull Key, the great door.
The summit (zig_3, temple_maps.py) is above them."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import town
import kit
import dprops
from dkit import Floor


def gong(F, rm, x, uid):
    """A gong on a room's north wall, x pixels from the room's west side."""
    X, Y = rm.p(x, 48)
    F.m.model("gong_wall", dprops.gong_wall, X, Y + 1, box=(-8, -5, 8, 0), frames=3, names=["gong_wall", "gong_wall_a", "gong_wall_b"], still=True,
              kind="gong", data={"id": uid}, lights=False)


def zig_1():
    F = Floor("zig_1", 3, 2, 'temple', dungeon='zig', label='1F', order=1, music='dungeon', seed=81)
    hall = F.room("hall", 1, 1, name="The First Hall")
    west = F.room("west", 0, 1, name="The Weighing Room")
    east = F.room("east", 2, 1, name="The Wall That Isn't")
    stair = F.room("stair", 1, 0, name="The Stair Hall")
    gap = F.room("gap", 0, 0, name="The Broken Floor")
    vault = F.room("vault", 2, 0, name="The Vessel Vault")
    F.link(1, 1, 's', 'out', to="temple_yard", spawn="door", name="south")
    F.link(1, 1, 'w'); F.link(1, 1, 'e')
    F.link(1, 1, 'n', 'lock', id="z1_door")
    F.link(1, 0, 'n', 'stairs', to="zig_2", spawn="south", name="top")
    F.link(1, 0, 'w')
    F.link(1, 0, 'e', 'bars', id="z1_vault", when="disc:z1_disc", say="The disc takes the light and holds it.^To the east, bars lift.")
    F.lay()
    F.carpet(hall, 196, 60, 24, 148, seed=1)
    F.carpet(stair, 196, 86, 24, 122, seed=2)
    F.dais(vault, 168, 96, 80, 52, seed=92)
    F.bake()
    # the first hall
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(hall, x, y)
    F.torch(hall, 44, 84); F.torch(hall, 372, 84)
    F.enemy(hall, "moth", 150, 150, "z1_m0"); F.enemy(hall, "moth", 270, 140, "z1_m1")
    # west: a block, a plate, and bars that lift on the map of the place
    F.partition_ns(west, 116, 48, 108)
    F.bars(west, 66, 108, "z1_bars", "plate:z1_plate", w=6.25, say="Somewhere in the wall, a weight drops. The bronze bars lift.")
    F.chest(west, 66, 86, "z1_map", "map_zig")
    F.block(west, 240, 152, "z1_block")
    F.plate(west, 176, 136, "z1_plate")
    F.torch(west, 372, 84)
    F.enemy(west, "sentinel", 300, 100, "z1_s1", once=True)
    for (x, y) in ((40, 196), (56, 200), (376, 196)):
        kit.pot(F.m, *west.p(x, y))
    # east: a wall only the waking world has, and the key behind it
    F.partition_ns(east, 250, 48, 208, layer=1)
    F.chest(east, 330, 124, "z1_key", "key")
    F.torch(east, 44, 84)
    F.enemy(east, "sentinel", 130, 150, "z1_s2", once=True)
    F.enemy(east, "moth", 180, 100, "z1_m2")
    # the stair hall: two sentinels, the stair, and a sun disc waiting for somebody to hand it the moon
    for (x, y) in ((120, 150), (296, 150)):
        F.pillar(stair, x, y)
    F.torch(stair, 150, 84); F.torch(stair, 266, 84)
    F.enemy(stair, "sentinel", 70, 100, "z1_s3", once=True)
    F.enemy(stair, "sentinel", 346, 100, "z1_s4", once=True)
    F.disc(stair, 350, "z1_disc")
    F.pool(stair, 350, 142, r=15)
    F.plaque(stair, 384, "{g}'NINHAL'S LAMP IS THE MOON. HIS FACE IS THE SUN.'{/}^{g}'HAND HIM HIS OWN LIGHT AND HE OPENS HIS HOUSE.'{/}^"
                         "The moon is on the floor, in a pool, through a hole in the roof. The sun is on the wall, and dull. Nothing is handing anything to anything.")
    # the broken floor: a chasm, a road of moonlight, and somebody's savings on the far side
    F.pit(gap, 150, 48, 290, 208, bridges=[[(296, 128), (240, 128), (240, 84), (196, 84), (196, 172), (144, 172)]], seed=57)
    F.chest(gap, 80, 124, "z1_coins", "shekels:30")
    F.torch(gap, 372, 84); F.torch(gap, 44, 190)
    F.enemy(gap, "moth", 340, 170, "z1_m3")
    # the vault
    F.chest(vault, 208, 128, "z1_vessel", "vessel")
    for (x, y) in ((120, 110), (296, 110)):
        F.pillar(vault, x, y)
    F.torch(vault, 60, 180); F.torch(vault, 356, 180)
    F.save()


def zig_2():
    """2F, the Halls of the Bull: the walk of fire, the counting room, the store, the Herdsman and
    what he keeps, and the bull's head that shuts the stair to anyone without a mirror."""
    F = Floor("zig_2", 3, 2, 'temple', dungeon='zig', label='2F', order=2, music='dungeon', seed=91)
    land = F.room("landing", 1, 1, name="The Landing")
    walk = F.room("walk", 0, 1, name="The Bull Walk")
    store = F.room("store", 2, 1, name="The Feed Store")
    count = F.room("count", 0, 0, name="The Counting Room")
    herd = F.room("herd", 1, 0, name="The Herdsman's Hall")
    gate = F.room("gate", 2, 0, name="The Bull's Gate")
    herd.mark = "mini"
    F.link(1, 1, 's', 'stairs', to="zig_1", spawn="top", name="south")
    F.link(1, 1, 'w'); F.link(1, 1, 'e')
    F.link(1, 1, 'n', 'lock', id="z2_door")
    F.link(0, 1, 'n')
    F.link(1, 0, 'e', 'bars', id="z2_gate", when="flag:dead_z2_herdsman")
    F.link(2, 0, 'n', 'stairs', to="zig_hi", spawn="south", name="top")
    F.lay()
    F.carpet(land, 196, 60, 24, 148, seed=1)
    F.carpet(herd, 196, 150, 24, 58, seed=2)
    F.dais(herd, 164, 52, 88, 50, seed=92)
    F.carpet(gate, 196, 60, 24, 60, seed=3)
    F.bake()
    m = F.m
    # the landing
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(land, x, y)
    F.torch(land, 44, 84); F.torch(land, 372, 84)
    F.plaque(land, 110, "{g}'THE BULLS OF NINHAL ARE WALKED AT DUSK, FED AT MIDNIGHT, AND NEVER, EVER PATTED.'{/}^Underneath, in a different hand: {g}'see the Herdsman about your fingers.'{/}")
    F.plaque(land, 30, "{g}'WEST, THE BULL WALK. WALK THE BULLS IN ORDER: THEY BREATHE IN ORDER.'{/}^{g}'A HERDSMAN COUNTS. A HERDSMAN WHO DOES NOT COUNT IS A SMELL.'{/}")
    F.enemy(land, "moth", 150, 150, "z2_m0"); F.enemy(land, "moth", 270, 140, "z2_m1")
    # the bull walk: four mouths in the north wall, breathing in turn, and the key at the far end
    for k, x in enumerate((336, 272, 144, 80)):
        F.bullhead(walk, x, 56, f"z2_h{k + 1}", straight=True, phase=0.6 * k)
    F.chest(walk, 40, 136, "z2_key", "key")
    F.torch(walk, 372, 196); F.torch(walk, 36, 196)
    # the counting room, off the walk: what the temple was owed, and two things to stop you taking it
    F.chest(count, 208, 96, "z2_coins", "shekels:50")
    for (x, y) in ((120, 110), (296, 110)):
        F.pillar(count, x, y)
    F.torch(count, 60, 180); F.torch(count, 356, 180)
    F.enemy(count, "sentinel", 120, 160, "z2_s1", once=True)
    F.enemy(count, "sentinel", 296, 160, "z2_s2", once=True)
    # the feed store: jars, moths, a sentinel, and a wall only the waking world keeps
    F.partition_ns(store, 280, 48, 208, layer=1)
    F.chest(store, 340, 128, "z2_vessel", "vessel")
    for (x, y) in ((40, 66), (56, 62), (72, 66), (40, 196), (56, 200), (200, 64), (216, 62), (232, 66), (248, 196)):
        kit.pot(m, *store.p(x, y), big=(x % 32 == 8))
    F.torch(store, 44, 130)
    F.enemy(store, "sentinel", 180, 150, "z2_s3", once=True)
    F.enemy(store, "moth", 120, 100, "z2_m2"); F.enemy(store, "moth", 330, 180, "z2_m3")
    # the Herdsman's hall: the keeper of the bulls, two of his herd in the wall, and the shield in its cage
    F.partition_ns(herd, 164, 48, 104)
    F.partition_ns(herd, 244, 48, 104)
    F.bars(herd, 208, 108, "z2_cage", "flag:dead_z2_herdsman", w=4.5)
    F.bigchest(herd, 208, 92, "z2_shield", "shield")
    F.bullhead(herd, 88, 56, "z2_hh1", herd=True); F.bullhead(herd, 328, 56, "z2_hh2", herd=True)
    for (x, y) in ((104, 150), (312, 150)):
        F.pillar(herd, x, y)
    F.torch(herd, 44, 196); F.torch(herd, 372, 196)
    F.enemy(herd, "herdsman", 208, 150, "z2_herdsman", once=True)
    # the bull's gate: the head that will not let anyone up the stair who cannot hand it its own fire
    F.partition(gate, 16, 188, 150, h=1.375)
    F.partition(gate, 228, 400, 150, h=1.375)
    F.bullhead(gate, 208, 150, "z2_bull")
    F.torch(gate, 60, 196); F.torch(gate, 356, 196)
    F.torch(gate, 150, 84); F.torch(gate, 266, 84)
    F.save()


def zig_hi():
    """3F, the High Halls: two sun discs for the door of the last hall, three mouths for the Bull
    Key, and the great door under the summit."""
    F = Floor("zig_hi", 3, 2, 'temple', dungeon='zig', label='3F', order=3, music='dungeon', seed=101)
    land = F.room("landing", 1, 1, name="The High Landing")
    west = F.room("west", 0, 1, name="The West Light")
    moon = F.room("moon", 0, 0, name="The Moon Room")
    door = F.room("door", 1, 0, name="The Great Door")
    mouths = F.room("mouths", 2, 1, name="The Three Mouths")
    keyr = F.room("key", 2, 0, name="The Key Room")
    door.mark = "boss"
    F.link(1, 1, 's', 'stairs', to="zig_2", spawn="top", name="south")
    F.link(1, 1, 'w'); F.link(1, 1, 'e')
    F.link(1, 1, 'n', 'bars', id="zh_bars", when="disc:zh_d1;disc:zh_d2", say="Both discs burn. The bars of the last hall lift.")
    F.link(0, 1, 'n')
    F.link(2, 1, 'n', 'bars', id="zh_keybars", when="flag:zh_h1;flag:zh_h2;flag:zh_h3", say="The third mouth breaks. Above it, bars lift.")
    F.link(1, 0, 'n', 'stairs', to="zig_3", spawn="south", name="top", door='big', id="z2_bigdoor", need="door_z2_bigdoor")
    F.lay()
    F.carpet(land, 196, 60, 24, 148, seed=1)
    F.carpet(door, 196, 86, 24, 122, seed=2)
    F.dais(keyr, 168, 96, 80, 52, seed=102)
    F.bake()
    m = F.m
    # the landing
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(land, x, y)
    F.torch(land, 44, 84); F.torch(land, 372, 84)
    F.plaque(land, 110, "{g}'TWO FACES OF THE SUN KEEP THE LAST HALL. NEITHER HAS SEEN THE MOON IN YEARS.'{/}^{g}'THREE MOUTHS KEEP THE KEY. ALL THREE HAVE SEEN YOU.'{/}")
    F.enemy(land, "sentinel", 120, 150, "zh_s1", once=True)
    # the west light: a pool, a disc, and a pit between
    F.disc(west, 120, "zh_d1")
    F.pool(west, 120, 150, r=15)
    F.torch(west, 372, 196); F.torch(west, 36, 196)
    F.enemy(west, "moth", 240, 150, "zh_m0"); F.enemy(west, "moth", 300, 100, "zh_m1")
    F.enemy(west, "sentinel", 280, 160, "zh_s2", once=True)
    # the moon room: the pool is across a drop that only a dreamer's road crosses
    F.pit(moon, 150, 48, 270, 208, bridges=[[(276, 128), (144, 128)]], seed=61)
    F.disc(moon, 80, "zh_d2")
    F.pool(moon, 80, 150, r=15)
    F.torch(moon, 372, 84); F.torch(moon, 372, 196)
    F.enemy(moon, "moth", 330, 150, "zh_m2")
    # the three mouths: all three look at whoever comes in, and all three have to be answered
    F.bullhead(mouths, 104, 56, "zh_h1"); F.bullhead(mouths, 312, 56, "zh_h3")
    F.bullhead(mouths, 208, 108, "zh_h2")
    F.partition(mouths, 136, 188, 108, h=1.375); F.partition(mouths, 228, 280, 108, h=1.375)
    for (x, y) in ((104, 170), (312, 170)):
        F.pillar(mouths, x, y)
    F.torch(mouths, 44, 196); F.torch(mouths, 372, 196)
    # the key room
    F.chest(keyr, 208, 128, "z2_bigkey", "bigkey")
    for (x, y) in ((120, 110), (296, 110)):
        F.pillar(keyr, x, y)
    F.torch(keyr, 60, 180); F.torch(keyr, 356, 180)
    # the great door
    for (x, y) in ((120, 150), (296, 150)):
        F.pillar(door, x, y)
    F.torch(door, 150, 84); F.torch(door, 266, 84)
    F.enemy(door, "sentinel", 70, 110, "zh_s3", once=True)
    F.enemy(door, "sentinel", 346, 110, "zh_s4", once=True)
    F.save()


if __name__ == "__main__":
    for w in sys.argv[1:] or ["zig_1"]:
        globals()[w]()
