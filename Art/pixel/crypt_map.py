"""The Crypt of the First Watch, under the old shrine on the olive terraces: where the night
watch of Ashkel buried its own, and kept two things for the night the city would not wake.

  den    run     lamps     .      .
  arms   walk    stair    beds  (beds)

The stair comes down from the shrine. West, along the watch's own walk, is the armoury, and the
blade behind a stone that has to be pushed. East is the dormitory, which is long, because the
watch was: the key is in it, behind olive roots only a blade cuts, with the jackals. North,
through the locked door, the hall of lamps, a stone and a plate; west of that the jackals' run,
which doubles back on itself, and at the end of it the den, its mother, and the Wakefire in its
cage. The way back out of the den was bricked up long ago. The dream never heard about the
bricks."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import kit
import dprops
from dkit import Floor, NW

BED = (-8, -26, 8, 0)


def bed(F, rm, x, y, k, text, sleeper=True):
    F.look(f"crypt_bed_{k if sleeper else 'empty'}", dprops.stone_bed(sleeper, k), rm, x, y, BED, text)


def rack(F, rm, x, text):
    X, Y = rm.p(x, NW)
    F.m.model("spear_rack", dprops.spear_rack(), X, Y + 2, box=(-13, -4, 13, 0), kind="look", data={"id": "say", "text": text}, shadow=False)


def crypt():
    F = Floor("crypt", 5, 2, 'crypt', dungeon='crypt', label='B1', order=1, music='crypt', seed=141)
    stair = F.room("stair", 2, 1, name="The Watch Stair", opts="dim")
    walk = F.room("walk", 1, 1, name="The Watch Walk", opts="dim")
    arms = F.room("arms", 0, 1, name="The Armoury", opts="dim")
    beds = F.room("beds", 3, 1, 2, 1, name="The Long Sleep", opts="dim")
    lamps = F.room("lamps", 2, 0, name="The Hall of Lamps", opts="dim")
    run = F.room("run", 1, 0, name="The Jackals' Run", opts="dim")
    den = F.room("den", 0, 0, name="The Den", opts="dim")
    den.mark = "mini"
    F.link(2, 1, 's', 'out', to="terraces", spawn="crypt", name="south")
    F.link(2, 1, 'w'); F.link(2, 1, 'e')
    F.link(1, 1, 'w')
    F.link(2, 1, 'n', 'lock', id="crypt_door")
    F.link(2, 0, 'w', 'bars', id="crypt_den", when="plate:crypt_plate", say="A weight drops somewhere in the wall.^To the west, bronze bars lift.")
    F.link(1, 0, 'w', 'bars', id="crypt_shut", when="flag:prequel_done", opts="shut:den")
    F.link(0, 1, 'n', 'bars', id="crypt_south", when="flag:item_wakefire")
    # the walk: a straight passage with a niche off it where the watch kept what it was not using
    walk.passage = True
    F.shape(walk, [(16, 92, 400, 164), (170, 48, 246, 92)])
    # the run: it goes round a pier of the living rock, the way a jackal would rather than a mason
    run.passage = True
    F.shape(run, [(16, 104, 150, 152), (104, 56, 150, 152), (104, 56, 312, 100), (266, 56, 312, 152), (266, 104, 400, 152)])
    F.lay()
    F.bake()
    m = F.m

    # ---------------------------------------------------------------- the stair
    for (x, y) in ((120, 112), (296, 112), (120, 184), (296, 184)):
        F.pillar(stair, x, y)
    F.torch(stair, 44, 84); F.torch(stair, 372, 84)
    F.plaque(stair, 110, "{g}'HERE LIES THE FIRST WATCH OF ASHKEL, WHO STAYED AWAKE SO THE CITY COULD SLEEP.'{/}^"
                         "{g}'IF THE CITY SLEEPS AND WILL NOT WAKE: TAKE THE BLADE. TAKE THE FLAME. WE HAVE KEPT BOTH.'{/}^"
                         "Underneath, smaller: {g}'WIPE YOUR FEET.'{/}")
    rack(F, stair, 312, "The First Watch's spears, racked for the night.^The bronze has gone green, and the shafts would not survive being picked up.| "
                        "One is missing. Somebody signed for it, presumably.")
    F.chest(stair, 340, 186, "crypt_map", "map_crypt")
    for (x, y) in ((40, 198), (56, 202), (376, 120)):
        kit.pot(m, *stair.p(x, y))

    # ---------------------------------------------------------------- the armoury: the blade, behind a stone
    # the watch walled its blade into the corner of the room and left one way in, with a stone in it
    F.partition(arms, 16, 120, 120, h=1.2)
    F.partition(arms, 136, 240, 120, h=1.2)
    F.partition_ns(arms, 240, 48, 120, h=1.2)
    F.block(arms, 128, 116, "crypt_block")
    F.bigchest(arms, 60, 84, "crypt_sword", "sword")
    F.plaque(arms, 300, "{g}'THE WATCH KEEPS ITS BLADE BEHIND STONE.'{/}^{g}'A WATCHMAN WHO CANNOT SHIFT THE STONE IS NOT READY FOR THE BLADE.'{/}^"
                        "Scratched underneath, by someone less patient: {g}'JUST PUSH IT, IDDIN.'{/}")
    rack(F, arms, 366, "Empty hooks, and the outline of a round shield in four hundred years of dust.^A clay label hangs where it hung: {g}'LENT TO THE TEMPLE. BRING IT BACK.'{/}")
    F.torch(arms, 372, 190); F.torch(arms, 268, 84); F.torch(arms, 36, 190)
    for (x, y) in ((200, 200), (216, 204), (384, 200)):
        kit.pot(m, *arms.p(x, y))

    # ---------------------------------------------------------------- the dormitory: the key, the roots, the jackals
    # the far end of the long room was walled off as a store; the jackals have it now, and the olive
    # trees up the hill have grown a door across the only way in
    F.partition(beds, 120, 240, 176, h=1.2)
    F.partition(beds, 288, 816, 176, h=1.2)
    F.partition_ns(beds, 112, 150, 208, h=1.2)
    F.roots(beds, 240, 288, 176, "crypt_roots",
            "Olive roots, come down through the roof looking for water and settled for a doorway.^They are as thick as your arm.| "
            "You could cut through them, if you had anything sharper than an opinion.")
    watch = "A watchman of the First Watch, off duty.^Four hundred years, and he has not once been late back."
    gone = "~~In the dream the bed is empty, and warm.^Wherever the First Watch goes at night, they don't take the stairs."
    bed(F, beds, 60, 84, 0, watch + gone)
    bed(F, beds, 116, 84, 1, "He was buried with his helmet on.^Regulations." + gone)
    bed(F, beds, 172, 84, 2, "Somebody left this one a cup of beer.^Somebody has drunk it.| You suspect the jackals. You hope it was the jackals." + gone)
    bed(F, beds, 244, 84, 3, watch + gone)
    bed(F, beds, 300, 84, 4, "This one is smiling.^It is the smile of a man whose relief turned up on time, once, and he never got over it." + gone)
    bed(F, beds, 356, 84, 0, "The last bed is empty, and made.^They are expecting somebody.| You decide not to work out who.", sleeper=False)
    F.chest(beds, 376, 200, "crypt_key", "key")
    F.enemy(beds, "jackal", 180, 196, "crypt_j0")
    F.enemy(beds, "jackal", 264, 192, "crypt_j1")
    F.enemy(beds, "jackal", 330, 198, "crypt_j2")
    for k, (x, y) in enumerate(((150, 200), (316, 190), (220, 204))):
        kit.bones(m, *beds.p(x, y), k)
    F.torch(beds, 36, 190); F.torch(beds, 372, 120); F.torch(beds, 788, 120); F.torch(beds, 600, 150)
    # ...and the far half of it: more of the watch, and what the jackals have been keeping at the end of their store
    bed(F, beds, 476, 84, 1, "This one has his boots on.^He meant to be up early." + gone)
    bed(F, beds, 532, 84, 2, "A watchman, and beside him a second, smaller pillow.^There is a dent in it the size of a cat.| There is no cat. You look." + gone)
    bed(F, beds, 588, 84, 3, watch + gone)
    bed(F, beds, 660, 84, 4, "Somebody carved a tally on the foot of this bed. Nights on duty.^It stops, and under it, in a different hand: {g}'RELIEVED.'{/}" + gone)
    bed(F, beds, 716, 84, 0, "He is holding a lamp with no oil in it.^Nobody has had the heart to take it off him. You are not going to be the first." + gone)
    bed(F, beds, 772, 84, 1, "The last sleeper in the row has turned his face to the wall.^Four hundred years of other people's snoring will do that." + gone)
    F.chest(beds, 792, 200, "crypt_hoard", "shekels:30")
    F.enemy(beds, "jackal", 520, 196, "crypt_j5")
    F.enemy(beds, "jackal", 690, 194, "crypt_j6")
    for k, (x, y) in enumerate(((456, 200), (600, 196), (740, 204))):
        kit.bones(m, *beds.p(x, y), k + 1)
    for (x, y) in ((430, 150), (446, 154), (800, 150)):
        kit.pot(m, *beds.p(x, y))
    for (x, y) in ((40, 196), (56, 200)):
        kit.pot(m, *beds.p(x, y))

    # ---------------------------------------------------------------- the watch walk, and the jackals' run
    F.torch(walk, 60, 100); F.torch(walk, 356, 100)
    rack(F, walk, 208, "The spare spears, in the niche where the watch kept what it was not using.^Also in the niche: a stool, a gaming board scratched on the floor, and four hundred years of somebody else's turn.")
    for (x, y) in ((182, 70), (234, 72)):
        kit.pot(m, *walk.p(x, y))
    kit.bones(m, *walk.p(300, 150), 1)
    F.torch(run, 126, 64); F.torch(run, 290, 64)
    F.enemy(run, "jackal", 208, 80, "crypt_j7")
    F.enemy(run, "jackal", 290, 130, "crypt_j8")
    for k, (x, y) in enumerate(((120, 140), (240, 90), (300, 70))):
        kit.bones(m, *run.p(x, y), k)

    # ---------------------------------------------------------------- the hall of lamps
    for (x, y) in ((104, 96), (312, 180), (104, 180)):
        F.pillar(lamps, x, y)
    for (x, y) in ((60, 150), (150, 196), (266, 196), (356, 150)):
        F.torch(lamps, x, y, light=3.8)
    F.block(lamps, 240, 168, "crypt_block2")
    F.plate(lamps, 176, 136, "crypt_plate")
    F.brazier(lamps, 152, 84, uid="crypt_l0"); F.brazier(lamps, 264, 84, uid="crypt_l1")
    F.plaque(lamps, 208, "{g}'TWO FIRES, FOR THE TWO HALVES OF THE NIGHT.'{/}^{g}'LIGHT BOTH, AND THE WATCH WILL REMEMBER YOU IN ITS WILL.'{/}")
    # what the watch left in its will
    F.partition_ns(lamps, 312, 48, 112)
    F.bars(lamps, 358, 118, "crypt_alcove", "lit:crypt_l0,crypt_l1", w=5.25, say="Both fires burn. In the corner, bars lift.^The watch keeps its word.")
    F.chest(lamps, 358, 92, "crypt_vessel", "vessel")
    # two of the pack keep the hall; the moths that come to its lamps are only there for a dreamer
    F.enemy(lamps, "jackal", 110, 150, "crypt_j3"); F.enemy(lamps, "jackal", 300, 120, "crypt_j4")
    F.enemy(lamps, "moth", 210, 184, "crypt_m0"); F.enemy(lamps, "moth", 60, 100, "crypt_m1")

    # ---------------------------------------------------------------- the den
    for (x, y) in ((92, 132), (324, 132), (128, 190), (288, 190)):
        F.pillar(den, x, y)
    F.partition_ns(den, 164, 48, 106)
    F.partition_ns(den, 244, 48, 106)
    F.bars(den, 208, 110, "crypt_cage", "flag:dead_crypt_mother", w=4.5)
    F.bigchest(den, 208, 92, "crypt_fire", "wakefire")
    X, Y = den.p(208, NW)
    m.model("plaque", dprops.plaque(), X, Y + 1, box=None, shadow=False)
    m.light(X, Y + 30, 3.4, (1.0, 0.72, 0.38), 0.55, h=0.7)                  # what is still burning in the chest
    # the way out that was bricked up: there when awake, not there asleep
    F.partition(den, 176, 240, 184, h=1.2, layer=1)
    F.partition_ns(den, 176, 182, 208, layer=1)
    F.partition_ns(den, 232, 182, 208, layer=1)
    F.enemy(den, "den_mother", 208, 150, "crypt_mother", once=True)
    for k, (x, y) in enumerate(((60, 80), (350, 96), (70, 196), (340, 196), (200, 160), (270, 120))):
        kit.bones(m, *den.p(x, y), k)
    for k, (x, y) in enumerate(((40, 120), (378, 180), (52, 172))):
        kit.urn(m, *den.p(x, y), k + 2)
    F.torch(den, 372, 84, light=3.6)
    for (x, y) in ((30, 66), (46, 62), (384, 196), (30, 200)):               # the watch's old jars: there is usually a little flame in one
        kit.pot(m, *den.p(x, y))
    F.save()


if __name__ == "__main__":
    crypt()
