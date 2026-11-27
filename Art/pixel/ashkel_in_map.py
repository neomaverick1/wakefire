"""Inside the houses of the gate square: twelve rooms, each its own screen. The watch house, the tower room
over it and the lock-up under it; Ilu-Bani's cellar, his hall and the rooms above; the tablet house and the
room where the master keeps what he takes off the boys; Widow Ilta's, and the room only her dream has; the
lamp seller's shop and his oil cellar."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import town
import kit
import houses
import hkit
import hin
import dkit
import dprops
from hin import House
from dkit import CW, CH, NW, SW, EW
from forge import Model, M, m_planks

NAME, OUT = "ashkel_in", "ashkel"


def build():
    F = House(NAME, 5, 5, music="town", seed=83)
    P = F.porch

    # ================================================================ the plan
    # ---- the watch house: the guardroom, the tower room, the lock-up
    guard = F.chamber("wt_guard", 0, 0, "The Watch House", 64, 352, 48, 176, more=[P(176)], plaster=('sandstone', 4.2), dado=('red', 2.8), band=('lines', 'red', 3.2), foot='stone', floor='flag',
                      hang=[(5.0, 'shield'), (7.0, 'tools'), (9.4, 'niche'), (16.6, 'niche')])
    tower = F.chamber("wt_tower", 1, 0, "The Tower Room", 144, 272, 64, 160, plaster=('sandstone', 4.0), dado=None, foot='stone', floor='plank',
                      hang=[(10.2, 'window'), (13.0, 'niche'), (15.8, 'window')])
    lock = F.chamber("wt_lock", 2, 0, "The Lock-up", 112, 304, 48, 128, more=[(176, 128, 304, 176)], opts="dim", plaster=('stone', 3.4), dado=None, foot='stone', floor='flag', beams=False,
                     hang=[(8.2, 'niche'), (17.6, 'tools')])
    # ---- Ilu-Bani's: the cellar, the hall, the rooms above
    mcel = F.chamber("mh_cellar", 3, 0, "Under Ilu-Bani's", 96, 320, 48, 160, opts="dim", plaster=('mud', 3.4), dado=None, foot='stone', floor='flag', beams=False,
                     hang=[(7.4, 'niche'), (18.6, 'niche')])
    hall = F.chamber("mh_hall", 4, 0, "Ilu-Bani's Hall", 64, 352, 48, 176, more=[P(176)], plaster=('limewash', 4.7), dado=('lapis', 3.0), band=('cones', 'cream', 4.2, 'red'), foot='stone', floor='tile',
                     hang=[(5.2, 'rug'), (7.6, 'niche'), (9.8, 'window'), (16.2, 'window'), (18.4, 'niche'), (20.8, 'rug')])
    upper = F.chamber("mh_upper", 0, 2, "The Rooms Above", 96, 320, 48, 160, more=[P(160)], plaster=('cream', 4.5), dado=('fig', 3.0), band=('zigzag', 'gold', 3.6, 'red'), floor='plank',
                      hang=[(7.2, 'window'), (9.4, 'niche'), (11.2, 'rug'), (14.8, 'rug'), (16.6, 'niche'), (18.8, 'window')])
    # ---- the tablet house, and what the master has taken away
    school = F.chamber("tb_school", 1, 2, "The Tablet House", 96, 400, 48, 176, more=[P(176)], plaster=('limewash', 4.3), dado=('ochre', 3.2), band=('writing', 'sandstone', 4.4), floor='earth',
                       hang=[(7.2, 'tablets'), (9.6, 'window'), (11.6, 'niche'), (14.4, 'niche'), (16.6, 'window'), (19.0, 'tablets'), (21.6, 'tablets')])
    kept = F.chamber("tb_kept", 2, 2, "Things Taken Away", 16, 240, 80, 176, more=[(176, 48, 240, 80)], plaster=('mud', 3.8), dado=None, floor='earth', beams=False,
                     hang=[(2.6, 'shelf'), (5.4, 'niche'), (8.2, 'shelf')])
    # ---- Widow Ilta's, and the room only her dream has
    ilta = F.chamber("il_room", 3, 2, "Widow Ilta's", 112, 400, 48, 176, more=[P(176)], plaster=('limewash', 4.6), dado=('blue', 3.2), band=('lines', 'blue', 3.4), floor='earth',
                     hang=[(8.4, 'herbs'), (10.8, 'niche'), (13.4, 'window'), (16.0, 'shelf'), (18.6, 'niche'), (21.2, 'cloth')])
    laid = F.chamber("il_dream", 4, 2, "The Table She Keeps", 16, 208, 80, 176, opts="dim", plaster=('lapis', 3.0), dado=None, floor='tile', beams=False, hang=[(6.6, 'niche')])
    # ---- the lamp seller's: the shop, and under it
    lamps = F.chamber("lp_shop", 0, 4, "The Lamp Seller's", 96, 320, 48, 176, more=[P(176)], opts="bright", plaster=('ochre', 4.6), dado=('red', 3.0), band=('zigzag', 'gold', 3.8, 'red'), floor='brick',
                      hang=[(7.0, 'niche'), (8.6, 'niche'), (10.2, 'niche'), (15.8, 'niche'), (17.4, 'niche'), (19.0, 'niche')])
    oil = F.chamber("lp_cellar", 1, 4, "The Oil Cellar", 128, 288, 48, 160, opts="dark", plaster=('mud', 3.2), dado=None, floor='flag', beams=False, hang=[])
    kept.secret = True
    laid.secret = True

    # ================================================================ the ways between them
    F.link(0, 0, 's', 'out', to=OUT, spawn="ak_watch", name="ak_watch_in")
    F.link(0, 0, 'n', 'stairs', to=NAME, spawn="wt_tower_dn", name="wt_guard_up")
    F.link(2, 0, 'n', 'stairs', to=NAME, spawn="wt_guard_dn", name="wt_lock_in")
    F.link(3, 0, 'n', 'stairs', to=NAME, spawn="mh_hall_dn", name="mh_cellar_in")
    F.link(4, 0, 's', 'out', to=OUT, spawn="ak_merchant", name="ak_merchant_in")
    F.link(4, 0, 'n', 'stairs', to=NAME, spawn="mh_upper_dn", name="mh_hall_up")
    F.link(0, 2, 's', 'out', to=OUT, spawn="ak_merchant_roof", name="ak_merchant_up")
    F.link(1, 2, 's', 'out', to=OUT, spawn="ak_tablets", name="ak_tablets_in")
    F.link(2, 2, 'n', 'stairs', to=OUT, spawn="ak_tablets_roof", name="ak_tablets_up")
    F.link(2, 2, 'w', 'bars', id="tb_way", when="on:tb_bolt",
           say="The bolt comes back, and the grille that the boys have looked through for years swings open.^It was never locked against thieves. It was locked against boys, which takes a better bolt.")
    F.link(3, 2, 's', 'out', to=OUT, spawn="ak_ilta", name="ak_ilta_in")
    F.link(4, 2, 'w', 'dream', id="il_way")
    F.link(0, 4, 's', 'out', to=OUT, spawn="ak_lamps", name="ak_lamps_in")
    F.link(1, 4, 'n', 'stairs', to=NAME, spawn="lp_shop_dn", name="lp_cellar_in")

    F.lay()
    T = F.T
    # ================================================================ on the floors, before the bake
    F.mat(guard, 92, 122, 88, 44, 1)
    F.platform(guard, 256, 48, 352, 108, h=12, steps=[(272, 304)], run=12)          # where the watch sleeps, off the cold of the floor
    F.rug(tower, 176, 100, 64, 36, 'carpet', 2)
    F.rug(hall, 80, 124, 76, 40, 'carpet', 3); F.rug(hall, 260, 124, 76, 40, 'lapis', 4, edge='gold')
    surround = T.rect(hall.ox + 168, hall.oy + 92, 80, 44)
    T.tiles(surround, seed=91, size=8, ramp='tile', base=4.2, checker='flag')
    T.border(surround, ramp='pale', tone=4.6, width=2, hgt=1.0)
    pool = T.rect(hall.ox + 176, hall.oy + 100, 64, 28)
    T.water(pool, seed=92, deep=8.0)
    T.border(pool, ramp='lapis', tone=3.4, width=1, hgt=0.8)
    F.rug(upper, 168, 100, 80, 40, 'carpet', 5)
    F.platform(school, 144, 48, 272, 92, h=8, steps=[(192, 224)], run=8)           # the master's end of the room
    F.mat(ilta, 184, 112, 72, 44, 6)
    F.rug(laid, 56, 104, 112, 48, 'lapis', 7, edge='gold')
    F.mat(lamps, 180, 140, 56, 28, 8)
    F.bake()
    m = F.m

    # ================================================================ what stands in them
    # ---- the guardroom
    F.put("in_table_game", hin.table_with(1.6, 0.9, things='game', seed=3), guard, 112, 150, box=(0, -14, 26, 0))
    F.put("in_stool", hin.stool(1), guard, 104, 148, box=(-3, -4, 3, 0)); F.put("in_stool", hin.stool(1), guard, 146, 148, box=(-3, -4, 3, 0))
    F.put("spear_rack", dprops.spear_rack(), guard, 160, 56, box=(-12, -4, 12, 2))
    F.put("in_hearth", hin.hearth, guard, 208, 132, box=(-7, -10, 7, -2), frames=3)
    F.put("in_water", hin.water_stand(1), guard, 76, 70, box=(-4, -5, 4, 0))
    for k, (x, y) in enumerate(((260, 72), (310, 72), (260, 94), (310, 94))):
        F.put("in_bunk", hin.bed_h(11, 'ochre'), guard, x, y, box=(0, -14, 35, 0))
    F.hatch(guard, 88, 96, "wt_hatch", NAME, "wt_lock_in", "wt_guard_dn", w=24, d=18)
    F.who(guard, 138, 136, "watch_a"); F.who(guard, 236, 72, "watch_b"); F.who(guard, 327, 67, "watch_c")
    F.say("in_tally_watch", hin.rack(1.3, 'tablets', 13, rows=1), guard, 300, 172, (0, -7, 21, 0),
          "The watch's book: who stood which night.^Forty nights back it stops. The last line says: {t}AZAR. GATE. (CHECK ON HIM.){/}| Nobody did.")
    F.lights(guard)
    # ---- the tower room
    F.chest(tower, 164, 150, "ak_wt_tower", "shekels:30")
    F.hatch(tower, 250, 146, "wt_tower_hatch", NAME, "wt_guard_up", "wt_tower_dn", w=24, d=18)
    F.put("lt_sacks", town.sacks(40), tower, 256, 84)
    F.say("in_stool_look", hin.stool(4), tower, 176, 82, (-3, -4, 3, 0),
          "The lookout's stool, under the window.^From here a man can see the whole of Ashkel, and nothing in it moving.| It is the dullest watch anybody ever stood, and you have stood most of them.")
    F.lights(tower)
    # ---- the lock-up
    F.bars(lock, 240, 134, "wt_cell", "on:wt_keys", w=8.0,
           say="The key turns. The cell door swings.^It is the first time in the history of the watch that anybody has broken INTO the lock-up.")
    X, Y = lock.p(140, NW)
    m.model("in_keys", hin.keys_peg(), X, Y + 2, box=(-6, -3, 6, 2), kind="latch", shadow=False,
            data={"id": "wt_keys", "say": "The cell keys, on a peg within reach of the cell.^The watch has never lost a prisoner this way. The watch has never had a prisoner who was awake."})
    F.put("in_cot", hin.bed(9, 'linen', made=False), lock, 184, 172, box=(0, -30, 16, 0))
    F.burrow_floor(lock, 284, 154, "wt_tunnel", "mh_tunnel")
    F.put("in_stool", hin.stool(1), lock, 128, 104, box=(-3, -4, 3, 0))
    F.put("in_basket", hin.basket(4), lock, 292, 60, box=(-4, -5, 4, 0))
    F.who(lock, 258, 160, "prisoner")
    F.lights(lock)
    # ---- under Ilu-Bani's
    F.put("in_logs_5", hin.logs(5, 1), mcel, 104, 110, box=(-4, -26, 30, 0))
    F.put("in_logs_4", hin.logs(4, 2), mcel, 108, 152, box=(-4, -26, 24, 0))
    F.put("in_jars_3", hin.big_jars(3, 1), mcel, 244, 70, box=(-6, -8, 26, 0))
    F.put("in_money", hin.money_pile(1), mcel, 230, 150, box=(-6, -8, 6, 0)); F.put("in_money_b", hin.money_pile(2), mcel, 304, 100, box=(-6, -8, 6, 0))
    F.chest(mcel, 180, 140, "ak_mh_cellar", "shekels:80")
    F.burrow_floor(mcel, 290, 136, "mh_tunnel", "wt_tunnel")
    F.say("in_logs_say", hin.logs(4, 3, l=1.2), mcel, 168, 86, (-4, -20, 24, 0),
          "Cedar, in the log, stacked to the beams.^The Temple paid for it twice. Ilu-Bani delivered it once. Both sides call this the usual arrangement.")
    F.lights(mcel)
    # ---- the hall
    X0, Y0 = hall.p(176, 100)
    m.solid(X0, Y0, X0 + 64, Y0 + 28)
    F.put("in_strongbox", hin.strongbox(1), hall, 104, 92, box=(-13, -13, 13, 0))
    F.put("in_tray", hin.tray_stand(), hall, 300, 100, box=(-5, -6, 5, 0))
    for k, (x, y, col) in enumerate(((92, 150, 'red'), (132, 154, 'gold'), (286, 152, 'blue'), (318, 148, 'fig'))):
        F.put(f"in_cushion_g_{col}", hin.cushion(col, k), hall, x, y, box=None)
    for k, x in enumerate((168, 248)):
        F.put(f"tub_palm_{k % 2}", hkit.tub_tree(k % 2, 'palm'), hall, x, 92, box=(-5, -8, 5, 0))
    F.put("in_lampstand", hin.lamp_stand, hall, 76, 76, box=(-3, -4, 3, 0), frames=2); F.put("in_lampstand", hin.lamp_stand, hall, 340, 76, box=(-3, -4, 3, 0), frames=2)
    F.hatch(hall, 328, 160, "mh_hatch", NAME, "mh_cellar_in", "mh_hall_dn", w=24, d=18)
    F.bar(hall, "ak_merchant_latch",
          say="A bar of cedar as thick as an arm, in bronze hooks. It lifts out.^Ilu-Bani barred his door against the whole of Ashkel. He did not think to bar his cellar against the watch house.")
    F.who(hall, 104, 106, "ilubani"); F.who(hall, 284, 108, "servant"); F.who(hall, 208, 150, "hound")
    F.lights(hall)
    # ---- the rooms above
    F.put("in_bed_great", hin.bed_h(21, 'fig', l=2.5, w=1.5), upper, 104, 94, box=(0, -24, 40, 0))
    F.put("in_bed_small_b", hin.bed_h(2, 'blue', l=1.7, w=0.85), upper, 282, 78, box=(0, -13, 27, 0))
    F.put("in_bed_small_r", hin.bed_h(1, 'red', l=1.7, w=0.85), upper, 282, 104, box=(0, -13, 27, 0))
    F.put("in_cradle", hin.cradle(1), upper, 152, 116, box=(0, -8, 14, 0))
    F.put("in_lampstand", hin.lamp_stand, upper, 244, 70, box=(-3, -4, 3, 0), frames=2)
    F.put("in_water", hin.water_stand(1), upper, 180, 70, box=(-4, -5, 4, 0))
    F.chest(upper, 116, 148, "ak_mh_upper", "vessel")
    F.hatch(upper, 236, 146, "mh_upper_hatch", NAME, "mh_hall_up", "mh_upper_dn", w=24, d=18)
    F.who(upper, 124, 84, "wife"); F.who(upper, 295, 73, "child_a"); F.who(upper, 295, 99, "child_b")
    F.lights(upper)
    # ---- the tablet house
    F.put("in_lesson", hin.lesson(), school, 176, 70, box=(-10, -4, 10, 0))
    F.put("in_stool", hin.stool(2), school, 244, 76, box=(-3, -4, 3, 0))
    for k, (x, y) in enumerate(((112, 128), (240, 128), (112, 160), (176, 160), (240, 160))):
        F.put("bench_1", hkit.bench(1.5, 1), school, x, y, box=(0, -6, 24, 0))
    F.put("bench_long", hkit.bench(2.5, 1), school, 164, 128, box=(0, -6, 40, 0))
    F.put("in_tabletchest", hin.tablet_chest(1), school, 300, 92, box=(0, -9, 14, 0))
    F.put("in_basket", hin.basket(4), school, 112, 92, box=(-4, -5, 4, 0))
    F.put("in_water", hin.water_stand(1), school, 330, 168, box=(-4, -5, 4, 0))
    F.who(school, 216, 74, "master"); F.who(school, 196, 80, "boy_a"); F.who(school, 184, 124, "boy_b"); F.who(school, 380, 64, "boy_c")
    F.say("in_lines", hin.rack(1.3, 'tablets', 9, rows=1), school, 290, 172, (0, -7, 21, 0),
          "A boy's lines. {t}I WILL NOT SLEEP IN CLASS.{/} Thirty-one times, neat as you like.^The thirty-second trails off down the tablet and over the edge.")
    F.lights(school)
    # ---- things taken away
    F.put("in_table_toys", hin.table_with(1.6, 0.9, things='toys', seed=5), kept, 60, 140, box=(0, -14, 26, 0))
    F.say("in_frog", hin.frog_jar(), kept, 124, 132, (-4, -5, 4, 0),
          "A jar with a cloth tied over it, and holes in the cloth.^Inside, a frog, asleep. It was confiscated forty-one nights ago. It has had the best of it.")
    F.put("in_basket", hin.basket(4), kept, 40, 168, box=(-4, -5, 4, 0))
    F.put("in_jars_2k", hin.big_jars(2, 4), kept, 150, 168, box=(-6, -8, 16, 0))
    F.chest(kept, 200, 150, "ak_tb_kept", "shekels:20")
    X, Y = kept.p(40, 80)
    m.model("in_bolt", hin.bolt(), X, Y + 2, box=(-6, -3, 6, 2), kind="latch", shadow=False,
            data={"id": "tb_bolt", "say": "A bronze bolt, on this side only, well oiled.^The master comes in by the roof, with a jug, when the boys have gone home. This is how he leaves."})
    F.lights(kept)
    # ---- Widow Ilta's
    F.put("in_table_figs", hin.table_with(1.5, 0.9, things='figs', seed=7), ilta, 204, 140, box=(0, -14, 24, 0))
    F.put("in_stool", hin.stool(1), ilta, 196, 138, box=(-3, -4, 3, 0)); F.put("in_stool", hin.stool(1), ilta, 236, 138, box=(-3, -4, 3, 0))
    F.put("in_hearth", hin.hearth, ilta, 320, 132, box=(-7, -10, 7, -2), frames=3)
    F.put("in_rack_jars", hin.rack(1.6, 'jars', 2), ilta, 124, 92, box=(0, -7, 26, 0))
    F.put("in_basket_figs", hin.basket(5, 'figs'), ilta, 300, 168, box=(-4, -5, 4, 0)); F.put("in_basket_figs", hin.basket(5, 'figs'), ilta, 316, 170, box=(-4, -5, 4, 0))
    F.put("in_loom_ilta", hin.loom(2, ('blue', 'linen'), 0.8), ilta, 352, 100, box=(0, -5, 24, 0))
    F.say("in_sandals", hin.sandals(), ilta, 176, 172, (-4, -4, 4, 0),
          "A man's sandals, by the door, toes to the street.^They have been oiled every week for forty years. They have not been anywhere.")
    F.say("in_figjars", hin.big_jars(3, 7), ilta, 130, 168, (-6, -8, 26, 0),
          "Figs in honey. Figs in wine. Figs dried on a string.^She has not eaten a fig in forty years. She says she is keeping them.")
    F.lights(ilta)
    # ---- the table she keeps
    F.put("in_table_figs", hin.table_with(1.5, 0.9, things='figs', seed=7), laid, 88, 140, box=(0, -14, 24, 0), layer=2)
    F.put("in_stool", hin.stool(1), laid, 80, 138, box=(-3, -4, 3, 0), layer=2); F.put("in_stool", hin.stool(1), laid, 120, 138, box=(-3, -4, 3, 0), layer=2)
    F.chest(laid, 168, 124, "ak_il_dream", "shekels:40", layer=2)
    F.say("in_sandals", hin.sandals(), laid, 40, 168, (-4, -4, 4, 0),
          "In here the sandals are wet, and there is dust on them from the road.^It is the only room in Ashkel that is tidier asleep than awake, and it is the one she never goes into.", layer=2)
    F.lights(laid)
    # ---- the lamp seller's
    F.put("in_counter_48", hin.counter(3.0, 0.6, seed=2, plaster=2), lamps, 112, 132, box=(0, -10, 48, 0))
    F.put("in_lamprack", hin.lamp_rack, lamps, 228, 62, box=(0, -7, 26, 0), frames=2)
    F.put("in_lamprack", hin.lamp_rack, lamps, 284, 62, box=(0, -7, 26, 0), frames=2)
    F.put("in_lampstand", hin.lamp_stand, lamps, 108, 104, box=(-3, -4, 3, 0), frames=2)
    F.put("in_table_lamps", hin.table_with(1.6, 0.9, things='lamps', seed=9), lamps, 250, 150, box=(0, -14, 26, 0))
    F.put("in_table_lamps", hin.table_with(1.6, 0.9, things='lamps', seed=9), lamps, 108, 172, box=(0, -14, 26, 0))
    F.put("in_lampstand", hin.lamp_stand, lamps, 304, 104, box=(-3, -4, 3, 0), frames=2)
    F.put("in_jars_2", hin.big_jars(2, 1), lamps, 290, 172, box=(-6, -8, 16, 0))
    F.hatch(lamps, 180, 100, "lp_hatch", NAME, "lp_cellar_in", "lp_shop_dn", w=24, d=18)
    F.who(lamps, 136, 118, "lampseller")
    F.enemy(lamps, "moth", 230, 120, "ak_lp_m1"); F.enemy(lamps, "moth", 280, 96, "ak_lp_m2"); F.enemy(lamps, "moth", 150, 160, "ak_lp_m3")
    F.lights(lamps)
    # ---- the oil cellar
    for j, y in enumerate((84, 104)):
        for i, x in enumerate(range(140, 196, 18)):
            F.pot(oil, x, y, True)
    F.say("in_oiljars", hin.big_jars(4, 9), oil, 228, 150, (-6, -8, 36, 0),
          "Lamp oil, to the brim, in jars taller than a boy.^He keeps it in the dark, on purpose. You are standing in it holding the Wakefire.| You stand very still, and then you leave the way you would leave a sleeping bull.")
    F.chest(oil, 268, 92, "ak_lp_cellar", "shekels:35")
    F.save()


if __name__ == "__main__":
    build()
