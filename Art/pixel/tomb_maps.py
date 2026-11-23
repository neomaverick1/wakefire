"""The tomb of Kurashtar, on the way to Kurashtar: three floors of halls dug into the Hill of
Sleepers. Not a block of rooms: an antechamber, a passage with the servants across it, wings
of different lengths, a walk the lamp bearers keep, a hall two halls long with a cut through
it, a court built to hold a morning that never came in; and over those the king's road, with
his birds on one side of it and his steward on the other.
  python3 tomb_maps.py [tomb_1 tomb_2 tomb_hi]"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import town
import necro
import kit
import dprops
import bprops
import tprops
import necro_maps as NM
from dkit import Floor, NW

SPIRIT = (0.45, 1.0, 0.85)


def gong_wall(F, rm, x, uid):
    """A gong on a room's north wall, x pixels from its west side."""
    X, Y = rm.p(x, NW)
    F.m.model("gong_wall", dprops.gong_wall, X, Y + 1, box=(-8, -5, 8, 0), frames=3, names=["gong_wall", "gong_wall_a", "gong_wall_b"], still=True,
              kind="gong", data={"id": uid}, lights=False)


def gong_stand(F, rm, x, y, uid):
    """A gong in a frame of its own, standing on the floor."""
    X, Y = rm.p(x, y)
    F.m.model("gong_stand", dprops.gong_stand, X, Y, box=(-11, -4, 11, 0), frames=3, names=["gong_stand", "gong_stand_a", "gong_stand_b"], still=True,
              kind="gong", data={"id": uid}, lights=False)


def cage(F, rm, x, y, uid, when, w=4.5, say=None):
    """An alcove against the north wall with a grille across its mouth."""
    half = int(w * 8)
    F.partition_ns(rm, x - half - 8, 48, y - 4)
    F.partition_ns(rm, x + half, 48, y - 4)
    F.bars(rm, x, y, uid, when, w=w, say=say)


def coffin(F, rm, x, y, open_=False):
    X, Y = rm.p(x, y)
    if open_:
        F.m.model("sarcophagus_open", necro.sarcophagus(2, True), X, Y, box=(-16, -14, 16, 0), kind="look", data={"id": "say", "text": NM.COFFIN_OPEN})
    else:
        F.m.model("sarcophagus", necro.sarcophagus(1), X, Y, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": NM.COFFIN})


def heap(F, rm, x, y, k, text="A king's treasure, heaped where the bearers set it down.^You are the night watch. You are the one man in Ashkel who can't."):
    X, Y = rm.p(x, y)
    F.m.model(f"treasure_{k % 4}", necro.treasure(k % 4), X, Y, box=(-12, -8, 12, 0), kind="look", data={"id": "say", "text": text})


def parked(F):
    """Pictures the game asks for by name while it runs (a bearer's lamp, the Sun Roller's sun), parked off the map's edge."""
    m = F.m
    m.model("hand_lamp", lambda fi: tprops.hand_lamp(fi), -100, -100, box=None, frames=3, lights=False, shadow=False)
    m.model("hand_lamp_out", tprops.hand_lamp(0, False), -100, -100, box=None, lights=False, shadow=False)
    m.model("gold_ball", lambda fi: tprops.gold_ball(fi), -100, -100, box=None, frames=4, lights=False, shadow=False)
    for v, key in (('front', 'f'), ('back', 'b'), ('side', 's'), ('flat', 'flat')):
        m.model(f"warden_door_{key}", tprops.warden_door(v), -100, -100, box=None, lights=False, shadow=False)
    kit.brazier_frames(m)


# ---------------------------------------------------------------------------------------------- 1F
def tomb_1():
    """1F, the Outer Halls: the antechamber the thieves got as far as, the servants in their one
    doorway, the offering store, the pillared hall and its stair, the treasury behind a lock with
    no waking key, the lamp walk, and the well."""
    F = Floor("tomb_1", 4, 3, 'tomb', dungeon='tomb', label='1F', order=1, music='tomb', seed=301)
    door = F.room("door", 1, 2, name="The Antechamber")
    serv = F.room("servants", 1, 1, name="The Hall of Servants")
    store = F.room("store", 0, 1, name="The Offering Store")
    hall = F.room("hall", 1, 0, name="The Pillared Hall")
    tre = F.room("treasury", 0, 0, name="The Treasury")
    walk = F.room("lampwalk", 2, 0, name="The Lamp Walk")
    well = F.room("well", 3, 0, name="The Well")
    F.link(1, 2, 's', 'out', to="necropolis", spawn="door", name="south")
    F.link(1, 2, 'n')
    F.link(1, 1, 'w')
    F.link(1, 1, 'n')
    F.link(1, 0, 'w')
    F.link(1, 0, 'e')
    F.link(2, 0, 'e')
    F.link(1, 0, 'n', 'stairs', to="tomb_2", spawn="south", name="top", door='lock', id="t1_door")
    # an eight-sided antechamber; a passage with a stub; an L; a pillared hall with its corners built up; a room
    # with two of them; a walk with a bay either side; a hall cut in two by its well
    F.corners(door, 32)
    serv.passage = True
    F.passage(serv, 'ns', 112, stubs='w')
    F.shape(store, [(16, 48, 400, 132), (232, 132, 400, 208)])
    F.corners(hall, 32)
    F.corners(tre, 32, which='ne se')
    walk.passage = True
    F.shape(walk, [(16, 88, 400, 168), (96, 48, 176, 88), (240, 168, 320, 208)])
    F.corners(well, 32)
    T = F.lay()
    F.carpet(door, 196, 60, 24, 148, seed=1)
    F.carpet(serv, 196, 48, 24, 160, seed=2)
    F.carpet(hall, 196, 110, 24, 98, seed=3)
    F.bake()
    m = F.m
    parked(F)

    # ---------------------------------------------------------------- the antechamber
    F.torch(door, 44, 84); F.torch(door, 372, 84)
    F.plaque(door, 110, "{g}'THE HOUSE OF KURASHTAR. HE IS IN. HE IS ALWAYS IN.'{/}^Under it, in charcoal, in a thief's hand: {g}'so are we, now.'{/}")
    F.plaque(door, 306, "{g}'LEAVE NOTHING. TAKE NOTHING. DISTURB NOTHING.'{/}^Under it, the same charcoal: {g}'1 goat (gold). 40 cups. rings, lots.'{/}| {g}'Kuri owes me a cup.'{/}")
    X, Y = door.p(124, 150)
    m.model("loot", necro.treasure(1), X, Y, box=(-12, -8, 12, 0), kind="look",
            data={"id": "say", "text": "Grave goods, bagged and ready to go.^They got this far forty nights ago. They have not got any further."})
    m.marker("npc", *door.p(96, 176), who="robber_a")
    m.marker("npc", *door.p(156, 186), who="robber_b")
    # what Zimu is dreaming about: there is always another one
    F.dreamthing(door, 136, 196, "t1_goat", "goat", "dream_goat", tprops.gold_goat(), box=(-7, -4, 7, 0), source=True)
    coffin(F, door, 316, 100)
    coffin(F, door, 330, 186, open_=True)
    for i, (x, y) in enumerate(((60, 120), (350, 140), (270, 200))):
        kit.urn(m, *door.p(x, y), i)
    F.enemy(door, "scarab", 270, 150, "t1_s0")

    # ---------------------------------------------------------------- the hall of servants
    # two stubs of wall narrow the passage to one doorway, and in the doorway stand three of the king's servants,
    # dead and on duty, shoulder to shoulder. They are there in the waking world and not in the dream; and in the
    # dream, where they are not, hangs the order they were left with
    F.partition(serv, 152, 188, 92, h=0.9)
    F.partition(serv, 228, 264, 92, h=0.9)
    for i, x in enumerate((196, 208, 220)):
        m.marker("npc", *serv.p(x, 88), who=f"servant_{i}")
    X, Y = serv.p(188, 76)
    m.solid(X, Y, X + 40, Y + 14, 1)
    m.marker("servants", X, Y, w=40, h=14)
    F.dreamthing(serv, 208, 86, "t1_order", "order", "dream_order", tprops.order(), box=None)
    F.torch(serv, 162, 190); F.torch(serv, 254, 190)
    F.look("stele_t1", town.stele(1.25, 1), serv, 60, 150, (-5, -5, 5, 0),
           "{g}'THE STAFF OF THE HOUSE STAND WHERE THEY WERE TOLD TO STAND.'{/}^{g}'THEY WERE TOLD ONCE. ONCE IS ENOUGH FOR GOOD STAFF.'{/}")
    for i, (x, y) in enumerate(((166, 60), (250, 60))):
        kit.urn(m, *serv.p(x, y), i + 3)

    # ---------------------------------------------------------------- the offering store
    X, Y = store.p(96, 112)
    m.model("scale", lambda fi: tprops.scale(fi == 1), X, Y, box=(-6, -8, 6, 0), frames=2, names=["scale", "scale_full"], still=True,
            kind="scale", data={"id": "t1_scale"}, lights=False)
    F.bars(store, 316, 170, "t1_storebars", "on:t1_scale", w=10.5,
           say="The pan goes down, and a grille goes up.^The king has been paid. He will want a receipt.")
    F.chest(store, 316, 196, "t1_map", "map_tomb")
    F.plaque(store, 250, "{g}'OFFERINGS TO THE KING ARE WEIGHED ON ARRIVAL. THE KING IS NOT.'{/}")
    for (x, y) in ((40, 66), (56, 62), (72, 66), (150, 62), (166, 66), (330, 62), (346, 66), (362, 62)):
        kit.pot(m, *store.p(x, y), big=(x % 32 == 8))
    F.torch(store, 200, 60); F.torch(store, 250, 196)
    F.enemy(store, "scarab", 180, 104, "t1_s1"); F.enemy(store, "scarab", 300, 100, "t1_s2")

    # ---------------------------------------------------------------- the pillared hall
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(hall, x, y)
    for x in (72, 136, 280, 344):
        Xn, Yn = hall.p(x, NW)
        m.model("sentinel_niche", necro.sentinel_niche(), Xn, Yn + 4, box=None)
    F.torch(hall, 44, 100); F.torch(hall, 372, 100)
    F.plaque(hall, 106, "{g}'KURASHTAR, KING OF ASHKEL, WHO DID NOT SLEEP.'{/}^Scratched under it, by somebody on his staff: {g}'AND WOULD NOT LET ANYONE ELSE.'{/}")
    F.chest(hall, 340, 186, "t1_fork", "fork_tomb")
    F.enemy(hall, "ushabti", 150, 150, "t1_g1", once=True)
    F.enemy(hall, "ushabti", 270, 140, "t1_g2", once=True)

    # ---------------------------------------------------------------- the treasury
    # the strongroom in its north-west corner: a wall, a grille, and a lock whose key is only anywhere in a dream
    F.partition_ns(tre, 132, 48, 118)
    F.dreamlock(tre, 74, 122, "t1_strong", w=7.25)
    F.chest(tre, 74, 92, "t1_key", "key")
    X, Y = tre.p(190, NW)
    m.model("hook", bprops.hook(), X, Y + 1, box=None, shadow=False)
    F.dreamthing(tre, 190, 0, "t1_dkey", "key", "dream_key", bprops.dream_key(), box=(-7, -4, 7, 0), wall=True)
    F.plaque(tre, 260, "{g}'THE KING'S TREASURY. KEPT BY HIS STEWARD, WHO KEEPS THE KEY ABOUT HIS PERSON.'{/}^{g}'HIS PERSON IS BURIED IN THE NEXT ROOM BUT ONE.'{/}")
    heap(F, tre, 300, 96, 0)
    heap(F, tre, 340, 186, 3)
    heap(F, tre, 220, 192, 2)
    X, Y = tre.p(60, 190)
    m.model("spoon", necro.treasure(1), X, Y, box=(-12, -8, 12, 0), kind="look",
            data={"id": "say", "text": "A thief's sack, and beside it a bronze spoon bent double.^Somebody tried the lock with it. The lock won."})
    F.torch(tre, 160, 196); F.torch(tre, 372, 130)

    # ---------------------------------------------------------------- the lamp walk
    F.plaque(walk, 136, "{g}'THE LAMPS OF THE KING ARE CARRIED, NEVER SET DOWN.'{/}^{g}'A BEARER WHO SETS HIS LAMP DOWN IS RELIEVED.'{/}| Nobody has ever been relieved.")
    F.enemy(walk, "bearer", 120, 128, "t1_b0", once=True)
    F.enemy(walk, "bearer", 300, 128, "t1_b1", once=True)
    for i, (x, y) in enumerate(((110, 62), (160, 62), (256, 198), (304, 198))):
        kit.urn(m, *walk.p(x, y), i + 1)

    # ---------------------------------------------------------------- the well
    F.pit(well, 152, 48, 264, 208, bridges=[[(146, 128), (270, 128)]], seed=41)
    F.chest(well, 336, 104, "t1_vessel", "vessel")
    F.torch(well, 60, 84); F.torch(well, 356, 196)
    F.look("stele_t1", town.stele(1.25, 1), well, 96, 180, (-5, -5, 5, 0),
           "{g}'THE WELL OF THE HOUSE. THE DEAD DO NOT DRINK.'{/}^{g}'IT IS HERE BECAUSE A HOUSE HAS ONE.'{/}")
    F.enemy(well, "scarab", 320, 160, "t1_s3"); F.enemy(well, "scarab", 100, 110, "t1_s4")
    for i, (x, y) in enumerate(((300, 64), (370, 120))):
        kit.urn(m, *well.p(x, y), i)
    F.save()


# ---------------------------------------------------------------------------------------------- 2F
def drawbridge(F, rm, x, y0, y1, uid, half=24):
    """A drawbridge across a drop that lies between y0 and y1, at x: standing on end on the far (north) lip
    until its rope is cut. The pit must have been made with planks=[(x - half, x + half)]."""
    m = F.m
    X, Yn = rm.p(x, y0)
    _, Ys = rm.p(x, y1)
    L = (y1 - y0 + 12) / 16.0
    m.model("drawbridge_down", tprops.drawbridge(L, half / 16.0), X, Yn - 6, box=None, kind="plank",
            data={"id": uid, "who": "bridge", "text": f"{X - half},{Yn},{X + half},{Ys}"}, lights=False, shadow=False)
    m.model("drawbridge_up", tprops.drawbridge(L, half / 16.0, up=True), X, Yn - 2, box=None, kind="bridgeup", data={"id": uid}, lights=False)
    rx = X + half + 12
    m.model("rope_span", tprops.rope((y1 - y0 + 10) / 16.0), rx, (Yn + Ys) // 2, box=None, kind="rope", data={"id": uid}, lights=False, shadow=False)
    m.model("rope_post", tprops.rope_post(), rx, Ys + 8, box=None, kind="look",
            data={"id": "say", "text": "A post, and a rope as thick as your wrist made fast to it.^The rope goes out over the drop to the top of the drawbridge. Cut it and the bridge comes down.| "
                                       "It is a long way out for a blade. Not for something thrown."})


def tomb_2():
    """2F, the Inner Halls: the hall of the lyre, two halls long with a cut through the middle of it; west, the
    bearers' way and the hall where a scarab keeps the sun; over that, the sun court; east, the wardens, the
    queen, and the brink."""
    F = Floor("tomb_2", 5, 3, 'tomb', dungeon='tomb', label='2F', order=2, music='tomb', seed=311)
    lyre = F.room("lyre", 2, 1, 1, 2, name="The Hall of the Lyre")
    wpass = F.room("westpass", 1, 1, name="The Bearers' Way")
    roller = F.room("roller", 0, 1, name="The Hall of the Sun")
    court = F.room("suncourt", 0, 0, name="The Sun Court")
    ward = F.room("wardens", 3, 1, name="The Wardens' Hall")
    queen = F.room("queen", 3, 2, name="The Queen's Room")
    brink = F.room("brink", 4, 0, 1, 2, name="The Brink")
    roller.mark = "mini"
    F.link(2, 2, 's', 'stairs', to="tomb_1", spawn="top", name="south")
    F.link(2, 1, 'n', 'stairs', to="tomb_hi", spawn="south", name="top", door='sun', id="t2_seal", need="door_t2_seal")
    F.link(2, 1, 'w')
    F.link(1, 1, 'w', 'bars', id="t2_rollerdoor", when="clear:roller", opts="shut:roller")
    F.link(0, 1, 'n', 'bars', id="t2_northbars", when="gong:t2_gong1",
           say="The gong sings, and bronze lifts in the north wall.^It is the first new sound in this hall in four hundred years. The dust does not know what to do.")
    F.link(2, 1, 'e', 'bars', id="t2_eastbars", when="gong:t2_gong0",
           say="The gong sings. To the east, bronze lifts.^Whatever is behind it has been listening for that note for a long time.")
    F.link(3, 1, 'e', 'bars', id="t2_brinkbars", when="clear:wardens",
           say="The last warden goes to pieces behind his door.^East of here, a grille lifts. Nobody is left to stand in front of it.")
    F.link(3, 1, 's')
    wpass.passage = True
    F.shape(wpass, [(16, 104, 230, 152), (186, 64, 230, 152), (186, 64, 400, 112), (354, 64, 400, 152)])
    F.corners(roller, 32)
    # the sun court: a low hall, and a chimney off its north-east corner with a wall across the mouth of it
    F.shape(court, [(16, 112, 400, 208), (336, 48, 400, 112)])
    F.corners(ward, 32)
    F.shape(queen, [(112, 48, 304, 176)])
    T = F.lay()
    F.carpet(lyre, 196, 60, 24, 166, seed=1)
    F.carpet(lyre, 196, 270, 24, 162, seed=2)
    # where to stand in the sun court, let into the floor in gold
    X, Y = court.p(320, 184)
    NM.sun_floor(T, X, Y, 15)
    F.bake()
    m = F.m
    parked(F)

    # ---------------------------------------------------------------- the hall of the lyre
    # a cut right across it that the dead filled with dark; a road of moonlight over it, for dreamers
    F.pit(lyre, 16, 232, 400, 264, bridges=[[(120, 226), (120, 270)]], seed=313)
    # this side of the cut: the stair he came up, one of the four fires, and somebody's savings
    F.brazier(lyre, 316, 340, "lyre_0")
    F.chest(lyre, 84, 400, "t2_coins", "shekels:40")
    F.look("stele_t2", town.stele(1.25, 1), lyre, 260, 300, (-5, -5, 5, 0),
           "{g}'THE CUT. THE DEAD FILLED IT WITH DARK, SO THAT NOBODY LIVING SHOULD CROSS.'{/}^{g}'NOBODY LIVING HAS.'{/}| There is a thief's sack on the far side.")
    F.enemy(lyre, "ushabti", 150, 360, "t2_g1", once=True)
    F.torch(lyre, 44, 300); F.torch(lyre, 372, 300); F.torch(lyre, 44, 410); F.torch(lyre, 372, 410)
    coffin(F, lyre, 330, 414)
    # the far side: the queen's lyre and the thief who has hold of it, the second fire, the door with the sun on it,
    # and a gong where no arm will reach it
    X, Y = lyre.p(288, 150)
    m.model("lyre", town.lyre(), X, Y, box=(-10, -8, 12, 0), kind="look", data={"id": "lyre"})
    m.marker("npc", *lyre.p(318, 176), who="robber_c")
    F.brazier(lyre, 96, 170, "lyre_1")
    F.pit(lyre, 308, 48, 372, 96, seed=314)
    gong_wall(F, lyre, 340, "t2_gong0")
    F.plaque(lyre, 110, "{g}'FOUR FIRES FOR THE FOUR WATCHES OF THE NIGHT. THEN HE WILL SEE YOU.'{/}^"
                        "Under it, smaller: {g}'THE FIRES ARE KEPT IN FOUR HALLS, SO THAT NO ONE SERVANT CAN LIGHT THEM ALL AND GET IT OVER WITH.'{/}")
    F.enemy(lyre, "ushabti", 150, 110, "t2_g2", once=True)
    F.enemy(lyre, "ushabti", 262, 200, "t2_g3", once=True)
    F.torch(lyre, 44, 100); F.torch(lyre, 268, 60)
    X, Y = lyre.p(60, 200)
    m.model("treasure_3", necro.treasure(3), X, Y, box=(-12, -8, 12, 0))

    # ---------------------------------------------------------------- the bearers' way
    F.enemy(wpass, "bearer", 100, 128, "t2_b0", once=True)
    F.enemy(wpass, "bearer", 300, 88, "t2_b1", once=True)
    for i, (x, y) in enumerate(((204, 76), (380, 140))):
        kit.urn(m, *wpass.p(x, y), i + 2)

    # ---------------------------------------------------------------- the hall of the sun
    # the great chest in its alcove, behind a grille that lifts when the hall is the beetle's no longer
    F.partition_ns(roller, 64, 48, 104)
    F.partition_ns(roller, 144, 48, 104)
    F.bars(roller, 108, 108, "t2_cage", "flag:dead_t2_roller", w=4.5)
    F.bigchest(roller, 108, 92, "t2_wheel", "wheel")
    # the way north, and the gong that opens it, over a drop
    F.pit(roller, 300, 48, 364, 96, seed=315)
    gong_wall(F, roller, 332, "t2_gong1")
    F.plaque(roller, 250, "{g}'THE KING'S SUN. IT IS CARRIED BEFORE HIM IN THE MORNING AND BEHIND HIM AT NIGHT.'{/}^{g}'IT IS NOT TO BE ROLLED.'{/}| "
                          "Something has been rolling something. There is a groove in the floor a hand deep.")
    F.torch(roller, 44, 100); F.torch(roller, 372, 100); F.torch(roller, 60, 196); F.torch(roller, 356, 196)
    m.marker("enemy", *roller.p(220, 150), who="sun_roller", id="t2_roller", text="once")

    # ---------------------------------------------------------------- the sun court
    # the wall across the chimney's mouth leaves a gap by the east wall; the east end of the hall under it is a drop,
    # so nothing thrown straight gets in: only something thrown at the sunrise, off the east wall
    F.partition(court, 336, 368, 120, h=0.5)
    F.pit(court, 352, 112, 400, 208, seed=316)
    gong_stand(F, court, 372, 70, "t2_gong2")
    # the third fire, in a cage against the court's north wall
    F.partition_ns(court, 52, 116, 168)
    F.partition_ns(court, 132, 116, 168)
    F.bars(court, 96, 172, "t2_altarbars", "gong:t2_gong2", w=4.5,
           say="Round the corner, off the wall, and home: the gong sings.^In front of the third fire, a grille lifts.")
    F.brazier(court, 96, 150, "lyre_2")
    F.look("stele_t2", town.stele(1.25, 1), court, 250, 140, (-5, -5, 5, 0),
           "{g}'THE SUN RISES IN THE EAST. IT IS ALWAYS LEAVING.'{/}^{g}'STAND ON THE SUN. THROW AT THE SUNRISE.'{/}| Somebody has added: {g}'it comes back. it is the only one that does.'{/}")
    F.torch(court, 44, 196); F.torch(court, 200, 122)

    # ---------------------------------------------------------------- the wardens' hall
    F.plaque(ward, 110, "{g}'THE WARDENS OF THE INNER DOOR. THEY DO NOT TURN THEIR BACKS.'{/}^{g}'THEY HAVE NEVER HAD TO.'{/}")
    F.enemy(ward, "warden", 150, 128, "t2_w0", once=True)
    F.enemy(ward, "warden", 290, 128, "t2_w1", once=True)
    F.torch(ward, 44, 100); F.torch(ward, 372, 100); F.torch(ward, 60, 196); F.torch(ward, 356, 196)

    # ---------------------------------------------------------------- the queen's room
    X, Y = queen.p(208, 92)
    m.model("sarcophagus", necro.sarcophagus(1), X, Y, box=(-16, -13, 16, 0), kind="look",
            data={"id": "say", "text": "The queen's coffin. The lid is on, and from inside there is no sound at all.^She is the one person in this tomb who is getting any rest."})
    F.plaque(queen, 150, "{g}'THE QUEEN. SHE ASKED TO BE BURIED FURTHER AWAY.'{/}^{g}'THIS WAS AS FAR AWAY AS THE KING WOULD ALLOW.'{/}| Her lyre is in the next hall. She asked about that, too.")
    F.chest(queen, 270, 150, "t2_vessel", "vessel")
    F.torch(queen, 130, 150)

    # ---------------------------------------------------------------- the brink
    F.pit(brink, 16, 200, 400, 264, seed=317, planks=[(184, 232)])
    drawbridge(F, brink, 208, 200, 264, "t2_bridge")
    F.brazier(brink, 208, 120, "lyre_3")
    F.plaque(brink, 110, "{g}'THE LAST WATCH.'{/}^{g}'THE BRIDGE IS RAISED AT NIGHT.'{/}| It has been night for four hundred years.")
    heap(F, brink, 80, 110, 1)
    heap(F, brink, 336, 130, 2)
    F.torch(brink, 44, 300); F.torch(brink, 372, 300); F.torch(brink, 44, 100); F.torch(brink, 372, 100)
    for i, (x, y) in enumerate(((60, 410), (350, 400), (120, 290))):
        kit.urn(m, *brink.p(x, y), i)
    F.save()


# ---------------------------------------------------------------------------------------------- 3F
def vulture(F, rm, x, y, uid):
    """One of the king's vultures, and the perch it keeps."""
    X, Y = rm.p(x, y)
    F.m.model("perch", tprops.perch(), X, Y - 1, box=(-3, -3, 3, 0), kind="look", lights=False,
              data={"id": "say", "text": "A bronze perch, a spear's length high. The bar is wound with hide, for talons.^Whatever sits on it is not small, and has not been fed."})
    F.enemy(rm, "vulture", x, y, uid, once=True)


def tomb_hi():
    """3F, the King's Road: the stair head, the crossing with a bird over it, the king's own door and the
    place where its keyhole was; east, the falconers' way, the mews and the roost; west, the clerks' passage
    and the steward's rest, where the Ghost Key is kept by a man who cannot pick it up."""
    F = Floor("tomb_hi", 4, 3, 'tomb', dungeon='tomb', label='3F', order=3, music='tomb', seed=331)
    head = F.room("stairhead", 1, 2, name="The Stair Head")
    wpass = F.room("westpass", 0, 2, name="The Clerks' Passage")
    stew = F.room("steward", 0, 0, 1, 2, name="The Steward's Rest")
    cross = F.room("crossing", 1, 1, name="The Crossing")
    thr = F.room("threshold", 1, 0, name="The King's Threshold")
    epass = F.room("eastpass", 2, 1, name="The Falconers' Way")
    mews = F.room("mews", 2, 0, 2, 1, name="The King's Mews")
    roost = F.room("roost", 3, 1, name="The Roost")
    F.link(1, 2, 's', 'stairs', to="tomb_2", spawn="top", name="south")
    F.link(1, 2, 'n')
    F.link(1, 2, 'w')
    F.link(0, 2, 'n', 'lock', id="t3_lock")
    F.link(1, 1, 'n')
    F.link(1, 1, 'e')
    F.link(1, 0, 'n', 'stairs', to="tomb_3", spawn="south", name="top", door='ghost', id="t3_kingdoor", need="door_t3_kingdoor")
    F.link(2, 1, 'n', 'bars', id="t3_mewsdoor", when="clear:mews", opts="shut:mews",
           say="The last of the king's birds comes down for good.^Behind you a grille lifts. In the corner, another: something small and bronze is in a chest behind it.")
    F.link(3, 0, 's')
    F.corners(head, 32)
    wpass.passage = True
    F.shape(wpass, [(152, 48, 264, 168), (152, 88, 400, 168)])
    # the steward's rest, two halls tall: a notch off its north-west corner, and rock where the rest of that end would be
    F.shape(stew, [(16, 112, 400, 432), (16, 48, 80, 112)])
    cross.passage = True
    F.shape(cross, [(152, 48, 264, 208), (152, 88, 400, 168)])
    F.corners(thr, 32)
    epass.passage = True
    F.shape(epass, [(16, 88, 264, 168), (152, 48, 264, 168)])
    F.corners(mews, 32)
    F.corners(roost, 32)
    T = F.lay()
    F.carpet(head, 196, 60, 24, 148, seed=1)
    F.carpet(thr, 196, 96, 24, 112, seed=2)
    # where to stand in the steward's rest (he has seen this sign before, one floor down)
    X, Y = stew.p(96, 183)
    NM.sun_floor(T, X, Y, 14)
    F.bake()
    m = F.m
    parked(F)

    # ---------------------------------------------------------------- the stair head
    F.torch(head, 44, 84); F.torch(head, 372, 84)
    F.look("stele_t3", town.stele(1.25, 1), head, 120, 150, (-5, -5, 5, 0),
           "{g}'THE KING'S ROAD. NONE WALK IT TWICE.'{/}^Under it, in a thief's charcoal: {g}'Abba went up. Abba has not come down. We are not going up.'{/}")
    for i, (x, y) in enumerate(((60, 120), (350, 150))):
        kit.urn(m, *head.p(x, y), i)
    F.enemy(head, "scarab", 150, 110, "t3_s0"); F.enemy(head, "scarab", 290, 120, "t3_s1"); F.enemy(head, "scarab", 300, 180, "t3_s2")

    # ---------------------------------------------------------------- the clerks' passage
    F.look("stele_t3", town.stele(1.25, 1), wpass, 360, 150, (-5, -5, 5, 0),
           "{g}'ALL REQUESTS FOR THE KEY ARE TO BE MADE IN WRITING.'{/}^{g}'ALL WRITING IS TO BE HANDED TO THE STEWARD.'{/}| {g}'THE STEWARD IS NOT TO BE DISTURBED.'{/}")
    F.enemy(wpass, "bearer", 320, 128, "t3_b0", once=True)
    F.enemy(wpass, "bearer", 208, 80, "t3_b1", once=True)
    F.torch(wpass, 164, 156)
    for i, (x, y) in enumerate(((240, 60), (384, 100))):
        kit.urn(m, *wpass.p(x, y), i + 1)

    # ---------------------------------------------------------------- the steward's rest
    # south of the drop: the way in, two wardens, and the post the drawbridge's rope is made fast to
    F.pit(stew, 16, 200, 400, 264, seed=333, planks=[(184, 232)])
    drawbridge(F, stew, 208, 200, 264, "t3_bridge")
    F.enemy(stew, "warden", 110, 340, "t3_w1", once=True)
    F.enemy(stew, "warden", 310, 330, "t3_w2", once=True)
    F.look("stele_t3", town.stele(1.25, 1), stew, 330, 410, (-5, -5, 5, 0),
           "{g}'THE STEWARD OF THE HOUSE RECEIVES NOBODY.'{/}^{g}'THIS IS NOT PERSONAL. HE RECEIVED NOBODY WHEN HE WAS ALIVE.'{/}")
    F.torch(stew, 44, 300); F.torch(stew, 372, 300); F.torch(stew, 44, 420); F.torch(stew, 372, 420)
    for i, (x, y) in enumerate(((60, 400), (130, 290))):
        kit.urn(m, *stew.p(x, y), i)
    # north of it: the steward, his coffin, the chest he cannot open behind a grille that a counterweight holds down;
    # and the counterweight, round a corner, over a drop, where only something thrown at the wall will find it
    F.partition(stew, 48, 80, 120, h=0.5)
    F.pit(stew, 16, 112, 64, 200, seed=334)
    X, Y = stew.p(44, 72)
    m.model("counterweight", tprops.counterweight(), X, Y, box=None, kind="rope", data={"id": "t3_weight", "who": "weight"}, lights=False, shadow=False)
    F.partition_ns(stew, 308, 112, 150)
    F.partition_ns(stew, 388, 112, 150)
    F.bars(stew, 352, 154, "t3_ghostcage", "on:t3_weight", w=4.5,
           say="With nothing holding it down, the grille in front of the steward's chest goes up.^He watches it go. He has the look of a man whose filing has been disturbed.")
    F.chest(stew, 352, 138, "t3_ghost", "ghostkey", ghost=True)
    coffin(F, stew, 170, 146)
    m.marker("npc", *stew.p(262, 166), who="steward")
    F.torch(stew, 120, 124); F.torch(stew, 290, 124)

    # ---------------------------------------------------------------- the crossing
    vulture(F, cross, 208, 126, "t3_v0")
    F.look("stele_t3", town.stele(1.25, 1), cross, 340, 152, (-5, -5, 5, 0),
           "{g}'EAST: THE KING'S BIRDS. NORTH: THE KING.'{/}^{g}'WEST: THE STEWARD, BY APPOINTMENT.'{/}| There is no way west from here. That is how you get an appointment.")
    F.torch(cross, 164, 196); F.torch(cross, 252, 196); F.torch(cross, 384, 100)

    # ---------------------------------------------------------------- the king's threshold
    F.plaque(thr, 110, "{g}'THE KING IS WITHIN. HE HAS BEEN WITHIN FOR FOUR HUNDRED YEARS.'{/}^{g}'KNOCK, AND IT WILL BE HELD AGAINST YOU.'{/}")
    F.brazier(thr, 150, 112, "t3_f0", lit=True); F.brazier(thr, 266, 112, "t3_f1", lit=True)
    for x in (72, 344):
        Xn, Yn = thr.p(x, NW)
        m.model("sentinel_niche", necro.sentinel_niche(), Xn, Yn + 4, box=None)
    F.enemy(thr, "ushabti", 90, 130, "t3_g1", once=True)
    F.enemy(thr, "ushabti", 326, 130, "t3_g2", once=True)
    heap(F, thr, 70, 190, 2)
    heap(F, thr, 350, 186, 0)

    # ---------------------------------------------------------------- the falconers' way
    F.plaque(epass, 180, "{g}'THE KING'S BIRDS ARE FED AT DAWN.'{/}^Under it, in a neat clerk's hand: {g}'THERE HAS NOT BEEN A DAWN. PLEASE ADVISE.'{/}")
    F.enemy(epass, "warden", 208, 104, "t3_w0", once=True)
    F.enemy(epass, "scarab", 70, 120, "t3_s3"); F.enemy(epass, "scarab", 110, 150, "t3_s4")
    F.torch(epass, 28, 100); F.torch(epass, 252, 156)
    kit.urn(m, *epass.p(40, 156), 2)

    # ---------------------------------------------------------------- the king's mews
    # four perches, two drops, and the birds; the small key in its cage in the corner
    F.pit(mews, 248, 96, 328, 176, seed=335)
    F.pit(mews, 520, 72, 600, 152, seed=336)
    vulture(F, mews, 130, 104, "t3_v1")
    vulture(F, mews, 410, 168, "t3_v2")
    vulture(F, mews, 470, 92, "t3_v3")
    vulture(F, mews, 690, 160, "t3_v4")
    F.enemy(mews, "scarab", 340, 190, "t3_s5"); F.enemy(mews, "scarab", 650, 100, "t3_s6")
    cage(F, mews, 740, 108, "t3_keycage", "clear:mews")
    F.chest(mews, 740, 92, "t3_key", "key")
    F.plaque(mews, 300, "{g}'THE KING'S MEWS. HE FLEW THEM AT HIS ENEMIES.'{/}^{g}'WHEN HE RAN OUT OF ENEMIES HE FLEW THEM AT HIS MINISTERS, TO KEEP THEIR HAND IN.'{/}")
    F.torch(mews, 44, 100); F.torch(mews, 60, 196); F.torch(mews, 400, 60); F.torch(mews, 780, 196); F.torch(mews, 640, 60)
    for i, (x, y) in enumerate(((180, 62), (560, 196), (430, 62))):
        kit.urn(m, *mews.p(x, y), i)

    # ---------------------------------------------------------------- the roost
    # a gong on an island in a drop, and the oldest of the birds watching whoever tries for it
    for (a, b, c, d) in ((120, 88, 296, 112), (120, 160, 296, 184), (120, 112, 184, 160), (232, 112, 296, 160)):
        F.pit(roost, a, b, c, d, seed=337 + a + b)
    gong_stand(F, roost, 208, 146, "t3_gong")
    cage(F, roost, 344, 108, "t3_vesselcage", "gong:t3_gong",
         say="The gong on its island sings.^In the corner, a grille lifts. The old bird does not look round. It has heard gongs.")
    F.chest(roost, 344, 92, "t3_vessel", "vessel")
    vulture(F, roost, 76, 150, "t3_v5")
    F.plaque(roost, 110, "{g}'THE ROOST. OLD BIRDS ARE NOT PUT DOWN. OLD BIRDS ARE PUT HERE.'{/}")
    F.torch(roost, 44, 196); F.torch(roost, 372, 196)
    F.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["tomb_1", "tomb_2", "tomb_hi"]
    for name in which:
        globals()[name]()
