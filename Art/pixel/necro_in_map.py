"""Inside the houses of the dead: nine rooms, each its own screen. Four on the Road of the Dead (the sweeper's,
the shepherd's, the room at the top of the stepped tomb, and the one with a bolt on the inside); five on the
Hill of Sleepers (a table laid for twelve, a man who knocks, a room whose owner is out, tablet nine of sixty,
and a night watchman's). Up here it is the dead who cannot sleep: in the waking world somebody is home in all
but one of them, in the dream there is nobody anywhere, and after the dawn they are all in bed at last.
  python3 necro_in_map.py [road | hill]"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import town
import kit
import hin
import necro
import tombs
from hin import House
from dkit import CW, CH, NW, SW, EW

BONE = ('bone', 4.5)
ABED = "~~In the dream it is only a stone box.~~Snoring.^At last."


# ------------------------------------------------------------------ the road of the dead
def road():
    NAME, OUT = "necro_road_in", "necro_road"
    F = House(NAME, 2, 3, music="hill", seed=97)
    P = F.porch
    sweep = F.chamber("nr_sweep", 0, 0, "Swept", 112, 304, 48, 176, more=[P(176)], opts="ghost", plaster=('bone', 5.0), dado=None, foot='stone', floor='tile', beams=False, fresh=True,
                      hang=[(8.4, 'spirit'), (13.0, 'moon'), (17.6, 'spirit')])
    sheep = F.chamber("nr_sheep", 1, 0, "Nine Thousand and Eight", 96, 320, 48, 176, more=[P(176)], opts="ghost", plaster=BONE, dado=('lapis', 2.8), band=('flock', 'lapis', 3.2, 'alabaster'),
                      foot='stone', floor='flag', beams=False, hang=[(7.6, 'spirit'), (10.2, 'tools'), (15.8, 'falsedoor'), (18.4, 'spirit')])
    high = F.chamber("nr_high", 0, 2, "A Little Higher Up", 112, 304, 48, 176, opts="ghost", plaster=BONE, dado=('red', 2.6), band=('lines', 'gold', 3.6), foot='stone', floor='flag', beams=False,
                     hang=[(8.4, 'spirit'), (10.6, 'moon'), (15.4, 'moon'), (17.6, 'spirit')])
    both = F.chamber("nr_both", 1, 2, "The Left-Hand Side", 80, 336, 48, 176, more=[P(176)], opts="ghost", plaster=BONE, dado=('fig', 2.8), foot='stone', floor='flag', beams=False,
                     hang=[(6.4, 'spirit'), (9.4, 'moon'), (16.6, 'moon'), (19.6, 'spirit')])

    F.link(0, 0, 's', 'out', to=OUT, spawn="nr_sweeper", name="nr_sweeper_in")
    F.link(1, 0, 's', 'out', to=OUT, spawn="nr_shepherd", name="nr_shepherd_in")
    F.link(0, 2, 'n', 'stairs', to=OUT, spawn="nr_proud_roof", name="nr_proud_up")
    F.link(1, 2, 's', 'out', to=OUT, spawn="nr_couple", name="nr_couple_in")

    F.lay()
    F.mat(sweep, 184, 148, 48, 22, 1)
    F.rug(sheep, 150, 118, 116, 44, 'lapis', 2, edge='pale')
    F.rug(high, 168, 104, 80, 48, 'carpet', 3)
    F.bake()
    m = F.m

    # ---- the sweeper's: nothing in it is out of place, and nothing in it has been used
    F.say("tb_coffin_a", necro.sarcophagus(1), sweep, 208, 86, (-16, -13, 16, -1),
          "Her coffin. The lid has been polished until she can see herself not sleeping in it." + ABED)
    F.say("tb_sandals", tombs.sandal_row(4), sweep, 128, 170, (0, -5, 26, 0),
          "Sandals, in a row by the door, toes to the wall. Other people's.^She makes callers take them off. Not one of them has ever come back for his.")
    F.say("tb_broom", tombs.broom_bucket(), sweep, 268, 76, (-3, -6, 13, 0),
          "A broom worn to a stump, and a bucket.^The water in the bucket is cleaner than most people's cups.")
    F.put("in_jars_3", hin.big_jars(3, 1), sweep, 122, 70, box=(-6, -8, 26, 0))
    for k, x in enumerate((140, 156, 172)):
        kit.urn(m, *sweep.p(x, 110), 2)
    F.who(sweep, 240, 128, "t_sweeper")
    F.lights(sweep)

    # ---- the shepherd's: his flock round the walls, his crook on its pegs, and him counting
    F.put("tb_bed", tombs.stone_bed(2.2, 1.0, 1), sheep, 190, 104, box=(0, -16, 35, 0))
    F.who(sheep, 208, 98, "t_shepherd")
    F.say("tb_sheep", tombs.stone_sheep(1), sheep, 128, 152, (-6, -5, 8, 0),
          "A sheep, cut in stone, at the foot of his bed where he can see it.^It has not blinked in three hundred years. He finds that it helps. Then he finds that it does not."
          "~~In the dream it is a stone, and has never looked like anything.~~A stone sheep.^Nobody is counting it.")
    F.put("in_stool", hin.stool(1), sheep, 250, 96, box=(-3, -4, 3, 0))
    F.put("in_water", hin.water_stand(1), sheep, 112, 70, box=(-4, -5, 4, 0))
    F.chest(sheep, 300, 152, "nr_sheep", "shekels:25")
    F.lights(sheep)

    # ---- the room at the top of the stepped tomb: in by the roof, and him standing on a block to be taller still
    F.put("tb_plinth", tombs.plinth(), high, 208, 136, box=(-9, -10, 9, 0))
    F.who(high, 208, 131, "t_proud")
    F.say("tb_coffin_b", necro.sarcophagus(2), high, 144, 84, (-16, -13, 16, -1),
          "His coffin, on a step of its own, so that even lying down he would be a hand higher than the man next door." + ABED)
    F.put("stone_seat", necro.stone_seat(), high, 276, 82, box=(-5, -8, 5, 0))
    F.chest(high, 284, 152, "nr_high", "shekels:40")
    F.lights(high)

    # ---- the one with the bolt on the inside: married fifty years, buried side by side, and still not settled
    F.put("tb_bed_two", tombs.double_bed(2.2, 2.3), both, 190, 112, box=(0, -37, 35, 0))
    F.who(both, 168, 132, "t_wife"); F.who(both, 250, 132, "t_husband")
    F.bar(both, "nr_couple_latch",
          say="The bolt slides back.^{g}'We bolted that,'{/} she says.| {g}'We did,'{/} he says.^It is the first thing they have agreed on since the funeral.")
    F.put("tb_table_cups", hin.table(1.5, 0.9, 0.5, 5, 'cups'), both, 96, 150, box=(0, -14, 24, 0))
    F.put("in_stool", hin.stool(1), both, 90, 128, box=(-3, -4, 3, 0)); F.put("in_stool", hin.stool(1), both, 126, 128, box=(-3, -4, 3, 0))
    F.say("tb_names", town.stele(1.1, 2), both, 316, 150, (-4, -4, 4, 0),
          "A stone with both their names on it.^His is first. Hers is bigger.| Somebody has since cut a line under his, and somebody else has cut a line through the line.")
    F.lights(both)
    F.save()


# ------------------------------------------------------------------ the hilltop
def hill():
    NAME, OUT = "necropolis_in", "necropolis"
    F = House(NAME, 3, 3, music="hill", seed=103)
    P = F.porch
    feast = F.chamber("np_feast", 0, 0, "Laid for Twelve", 64, 352, 48, 176, more=[P(176)], opts="ghost", plaster=('bone', 4.8), dado=('lapis', 3.0), band=('cones', 'cream', 4.2, 'red'),
                      foot='stone', floor='tile', beams=False, hang=[(5.4, 'spirit'), (8.0, 'rug'), (10.6, 'spirit'), (15.4, 'spirit'), (18.0, 'rug'), (20.6, 'spirit')])
    knock = F.chamber("np_knock", 1, 0, "Is Anybody There", 112, 304, 48, 176, more=[P(176)], opts="ghost", plaster=BONE, dado=None, foot='stone', floor='flag', beams=False,
                      hang=[(8.4, 'spirit'), (13.0, 'moon'), (17.6, 'spirit')])
    five = F.chamber("np_five", 2, 0, "Back in Five Minutes", 128, 288, 48, 176, more=[P(176)], opts="dim", plaster=BONE, dado=('ochre', 3.0), foot='stone', floor='flag', beams=False,
                     hang=[(10.0, 'falsedoor'), (16.2, 'moon')])
    read = F.chamber("np_read", 0, 2, "Tablet Nine of Sixty", 80, 336, 48, 176, more=[P(176)], opts="ghost", plaster=BONE, dado=None, band=('writing', 'stone', 4.4), foot='stone', floor='flag', beams=False,
                     hang=[(6.6, 'tablets'), (9.6, 'spirit'), (12.4, 'tablets'), (15.4, 'tablets'), (18.4, 'spirit')])
    pill = F.chamber("np_pill", 1, 2, "Three Hundred Years Owed", 128, 288, 48, 176, more=[P(176)], opts="ghost", plaster=BONE, dado=('red', 2.6), foot='stone', floor='flag', beams=False,
                     hang=[(9.6, 'shield'), (13.0, 'spirit'), (16.4, 'tools')])

    F.link(0, 0, 's', 'out', to=OUT, spawn="np_rich", name="np_rich_in")
    F.link(1, 0, 's', 'out', to=OUT, spawn="np_knocker", name="np_knocker_in")
    F.link(2, 0, 's', 'out', to=OUT, spawn="np_five", name="np_five_in")
    F.link(0, 2, 's', 'out', to=OUT, spawn="np_reader", name="np_reader_in")
    F.link(1, 2, 's', 'out', to=OUT, spawn="np_pillow", name="np_pillow_in")

    F.lay()
    F.rug(feast, 120, 96, 176, 60, 'lapis', 1, edge='gold')
    F.mat(knock, 184, 148, 48, 22, 2)
    F.rug(read, 150, 112, 116, 44, 'carpet', 4)
    F.mat(pill, 150, 120, 64, 30, 5)
    F.bake()
    m = F.m

    # ---- a table laid for twelve, and one man at it
    F.put("tb_banquet", tombs.banquet(5.0, 1.0), feast, 168, 134, box=(0, -16, 80, 0))
    for k, x in enumerate((184, 208, 232)):
        F.put("in_stool", hin.stool(1), feast, x, 112, box=(-3, -4, 3, 0)); F.put("in_stool", hin.stool(1), feast, x, 148, box=(-3, -4, 3, 0))
    F.put("stone_seat", necro.stone_seat(), feast, 150, 132, box=(-5, -8, 5, 0))
    F.who(feast, 150, 126, "t_rich")
    F.say("tb_coffin_c", necro.sarcophagus(3), feast, 96, 84, (-16, -13, 16, -1),
          "His coffin: alabaster, banded in gold, and never slept in.^He says it is for after the guests have gone." + ABED)
    F.put("in_jars_3", hin.big_jars(3, 1), feast, 280, 70, box=(-6, -8, 26, 0))
    F.chest(feast, 330, 150, "np_feast", "shekels:60")
    F.lights(feast)

    # ---- the man who knocks: his stool by the door, and the hole the robbers came up through
    F.put("in_stool", hin.stool(1), knock, 252, 164, box=(-3, -4, 3, 0))
    F.who(knock, 250, 148, "t_knocker")
    F.say("tb_coffin_d", necro.sarcophagus(4, open_=True), knock, 180, 86, (-16, -13, 22, -1),
          "His coffin, the lid off and stood against it.^He has not been in it since the first night. He could not hear the door from in there."
          "~~In the dream it is only a stone box.~~The lid is back on.^From inside: nothing at all. He has stopped listening.")
    F.burrow_floor(knock, 136, 150, "kn_tunnel", "fv_tunnel")
    F.say("tb_sacks", town.sacks(40), knock, 280, 80, (-9, -8, 9, 0),
          "Sacks, empty. Somebody came up through the floor with these, a long time ago, and went away again without filling them.^He kept them. They were company.")
    F.lights(knock)

    # ---- back in five minutes
    F.say("tb_coffin_e", necro.sarcophagus(5, open_=True), five, 180, 86, (-16, -13, 22, -1),
          "An empty coffin, the lid pushed off.^Whoever it is got up, wrote on the door, and went out.| The bar is across the door on the inside."
          "~~In the dream it is only a stone box.~~An empty coffin, the lid pushed off.^Still out.")
    F.say("in_sandals", hin.sandals(), five, 236, 104, (-3, -4, 3, 0),
          "Slippers, side by side, toes to the door.^She said she would only be a minute.")
    F.say("tb_table_cups", hin.table(1.5, 0.9, 0.5, 5, 'cups'), five, 138, 150, (0, -14, 24, 0),
          "A table, and a cup on it, still full.^The dust has made a skin on it you could write in.")
    F.burrow_floor(five, 260, 128, "fv_tunnel", "kn_tunnel")
    F.chest(five, 268, 156, "np_five", "vessel", ghost=True)
    F.bar(five, "np_five_latch",
          say="The bar lifts out of its hooks, and the door with BACK IN FIVE MINUTES on it swings open.^It was barred from the inside. Whoever went out did not go out this way.| You decide not to think about that.")
    F.lights(five)

    # ---- tablet nine of sixty
    F.put("in_table_tabs", hin.table(1.6, 0.9, 0.5, 7, 'tablets'), read, 150, 128, box=(0, -14, 26, 0))
    F.who(read, 196, 124, "t_scribe")
    F.put("stone_seat", necro.stone_seat(), read, 262, 128, box=(-5, -8, 5, 0))
    F.who(read, 262, 122, "t_listener")
    F.say("in_rack_tabs", hin.rack(1.6, 'tablets', 9, rows=2), read, 92, 166, (0, -7, 26, 0),
          "Tablets one to eight of sixty, in order, well thumbed.^Tablets ten to sixty are in the crate. The crate has not been opened.")
    F.put("in_tabchest", hin.tablet_chest(3), read, 308, 160, box=(-8, -9, 8, 0))
    F.say("tb_coffin_f", necro.sarcophagus(6), read, 300, 84, (-16, -13, 16, -1),
          "Two coffins' worth of stone, cut as one, with a shelf let into the side for tablets." + ABED)
    F.lights(read)

    # ---- the night watchman's
    F.put("tb_bed", tombs.stone_bed(2.2, 1.0, 1), pill, 196, 96, box=(0, -16, 35, 0))
    F.who(pill, 190, 112, "t_watchman")
    F.say("tb_rattle", hin.stool(4), pill, 150, 164, (-3, -4, 3, 0),
          "A watchman's stool, three legs, one shorter than the others.^So that whoever sat on it could not nod off without finding out.| You had one just like it. You managed.")
    F.chest(pill, 268, 152, "np_pill", "shekels:30")
    F.lights(pill)
    F.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["road", "hill"]
    if "road" in which: road()
    if "hill" in which: hill()
