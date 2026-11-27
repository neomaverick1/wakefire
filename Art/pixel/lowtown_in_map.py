"""Inside the houses of Lower Ashkel: fifteen rooms, each its own screen. Hesha's bakery with the
bedroom over it and the flour cellar under it; the Seven Jars and what is under that; Kesh's
pottery and the cash room he walled himself into; the weavers' and the room on their roof; the
house the goat stands on; the counting house and its strongroom; Ummi's, and the room only a
dreamer can walk into; the net loft."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import town
import kit
import houses
import hkit
import hin
import dkit
from hin import House
from dkit import CW, CH, NW, SW, EW
from forge import Model, M, m_planks

NAME, OUT = "lowtown_in", "lowtown"


def _tub(colour):
    m = Model()
    houses.tub(m, hin.MT, 0, 0.35, 0.46, colour)
    return m


def build():
    F = House(NAME, 5, 5, music="town", seed=61)
    P = F.porch

    # ================================================================ the plan
    # ---- the bakery: shop, bedroom over it, cellar under it
    shop = F.chamber("bk_shop", 0, 0, "Hesha's Bakery", 112, 304, 48, 176, more=[P(176)], plaster=('limewash', 4.4), dado=('red', 3.2), band=('lines', 'red', 3.4), floor='brick',
                     hang=[(8.2, 'bread'), (10.4, 'niche'), (15.6, 'niche'), (17.7, 'herbs')])
    bed = F.chamber("bk_bed", 1, 0, "Over the Shop", 128, 288, 48, 160, more=[P(160)], plaster=('ochre', 4.4), dado=('blue', 3.0), floor='plank',
                    hang=[(9.3, 'window'), (11.2, 'niche'), (13.0, 'rug'), (14.9, 'niche'), (16.7, 'window')])
    cellar = F.chamber("bk_cellar", 2, 0, "The Flour Cellar", 144, 272, 48, 144, opts="dim", plaster=('mud', 3.6), dado=None, floor='flag', beams=False,
                       hang=[(10.0, 'niche'), (16.2, 'tools')])
    # ---- the Seven Jars: the hall, and under it
    hall = F.chamber("beer_hall", 3, 0, "The Seven Jars", 64, 352, 48, 176, more=[P(176)], plaster=('ochre', 4.1), dado=('red', 2.8), band=('zigzag', 'ochre', 3.6, 'red'), floor='earth',
                     hang=[(5.2, 'cups'), (7.5, 'niche'), (9.8, 'cups'), (13.0, 'shield'), (16.2, 'cups'), (18.5, 'niche'), (20.7, 'cups')])
    under = F.chamber("beer_cellar", 4, 0, "Under the Seven Jars", 112, 304, 48, 160, more=[P(160)], opts="dim", plaster=('mud', 3.3), dado=None, floor='flag', beams=False,
                      hang=[(8.2, 'niche'), (10.4, 'tools')])
    # ---- the pottery: the shop, and the cash room he walled himself into
    pots = F.chamber("pt_shop", 0, 2, "Kesh's Pottery", 160, 400, 48, 176, more=[P(176)], plaster=('cream', 4.2), dado=('ochre', 3.4), band=('cones', 'clay', 4.0, 'dark'), floor='earth',
                     hang=[(11.0, 'shelf'), (13.4, 'shelf'), (15.8, 'niche'), (18.2, 'shelf'), (20.6, 'shelf'), (23.0, 'niche')])
    cash = F.chamber("pt_cash", 1, 2, "The Cash Room", 16, 240, 80, 176, more=[(176, 48, 240, 80)], plaster=('cream', 3.8), dado=('ochre', 3.0), floor='tile',
                     hang=[(2.6, 'tablets'), (5.2, 'niche'), (8.0, 'tablets')])
    # ---- the weavers': the workroom, and the room on the roof
    work = F.chamber("wv_work", 2, 2, "The Weavers'", 80, 336, 48, 176, plaster=('limewash', 4.5), dado=('blue', 3.2), band=('zigzag', 'blue', 3.4, 'cream'), floor='earth',
                     hang=[(6.4, 'cloth'), (8.8, 'niche'), (17.2, 'niche'), (19.6, 'cloth')])
    loft = F.chamber("wv_upper", 3, 2, "The Sisters' Room", 128, 288, 64, 176, more=[P(176)], plaster=('limewash', 4.3), dado=('fig', 3.0), floor='plank',
                     hang=[(9.2, 'window'), (11.4, 'niche'), (14.6, 'niche'), (16.8, 'window')])
    # ---- the house the goat stands on
    goat = F.chamber("goat_room", 4, 2, "The Goat's House", 128, 288, 48, 160, more=[P(160)], plaster=('sandstone', 4.0), dado=('green', 2.8), floor='earth',
                     hang=[(9.2, 'window'), (16.8, 'herbs')])
    # ---- the counting house and its strongroom
    tax = F.chamber("tax_office", 0, 4, "The Counting House", 112, 400, 48, 176, more=[P(176)], plaster=('sandstone', 4.2), dado=None, band=('writing', 'sandstone', 4.4), foot='stone', floor='tile',
                    hang=[(8.4, 'tablets'), (10.8, 'tablets'), (13.2, 'niche'), (15.6, 'tablets'), (18.0, 'tablets'), (20.4, 'niche'), (22.8, 'tablets')])
    vault = F.chamber("tax_vault", 1, 4, "The Strongroom", 16, 176, 96, 176, opts="dim", plaster=('stone', 3.6), dado=None, foot='stone', floor='flag', beams=False,
                      hang=[(3.0, 'niche'), (8.6, 'niche')])
    # ---- Ummi's, and the room only a dreamer has
    ummi = F.chamber("or_room", 2, 4, "Ummi's House", 112, 400, 48, 176, more=[P(176)], plaster=('limewash', 4.6), dado=('fig', 3.2), band=('zigzag', 'lapis', 3.4, 'gold'), floor='sand',
                     hang=[(8.4, 'rug'), (11.0, 'niche'), (13.6, 'herbs'), (16.6, 'niche'), (19.4, 'rug'), (22.4, 'herbs')])
    seen = F.chamber("or_dream", 3, 4, "What She Sees", 16, 208, 80, 176, opts="dim", plaster=('lapis', 3.0), dado=None, floor='tile', beams=False, hang=[(6.6, 'niche')])
    # ---- the net loft
    nets = F.chamber("net_loft", 4, 4, "The Net Loft", 96, 320, 48, 176, more=[P(176)], plaster=('mud', 3.9), dado=None, floor='plank',
                     hang=[(7.6, 'net'), (10.8, 'tools'), (16.4, 'net'), (18.8, 'window')])
    cash.secret = True
    seen.secret = True

    # ================================================================ the ways between them
    F.link(0, 0, 's', 'out', to=OUT, spawn="lt_bakery", name="lt_bakery_in")
    F.link(0, 0, 'n', 'stairs', to=NAME, spawn="bk_bed_dn", name="bk_shop_up")
    F.link(1, 0, 's', 'out', to=OUT, spawn="lt_bakery_roof", name="lt_bakery_up")
    F.link(2, 0, 'n', 'stairs', to=NAME, spawn="bk_shop_dn", name="bk_cellar_in")
    F.link(3, 0, 's', 'out', to=OUT, spawn="lt_beer", name="lt_beer_in")
    F.link(4, 0, 'n', 'stairs', to=NAME, spawn="beer_hall_dn", name="beer_cellar_top")
    F.link(4, 0, 's', 'out', to=OUT, spawn="lt_beer_cellar", name="lt_beer_cellar_in")
    F.link(0, 2, 's', 'out', to=OUT, spawn="lt_pottery", name="lt_pottery_in")
    F.link(1, 2, 'w', 'crack', id="pt_crack",
           text="The plaster here is newer than the wall, and worse.^Somebody bricked up a doorway from the far side, in a hurry, and plastered what he could reach.")
    F.link(1, 2, 'n', 'stairs', to=OUT, spawn="lt_pottery_roof", name="lt_pottery_up")
    F.link(2, 2, 'n', 'stairs', to=NAME, spawn="wv_upper_dn", name="wv_work_up")
    F.link(3, 2, 's', 'out', to=OUT, spawn="lt_weavers_roof", name="lt_weavers_up")
    F.link(4, 2, 's', 'out', to=OUT, spawn="lt_goat", name="lt_goat_in")
    F.link(4, 2, 'n', 'stairs', to=OUT, spawn="lt_goat_roof", name="lt_goat_up")
    F.link(0, 4, 's', 'out', to=OUT, spawn="lt_tax", name="lt_tax_in")
    F.link(1, 4, 'w', 'lock', id="tax_lock")
    F.link(2, 4, 's', 'out', to=OUT, spawn="lt_oracle", name="lt_oracle_in")
    F.link(3, 4, 'w', 'dream', id="or_way")
    F.link(4, 4, 's', 'out', to=OUT, spawn="lt_netloft", name="lt_netloft_in")

    F.lay()
    # ================================================================ on the floors, before the bake
    F.mat(shop, 180, 136, 56, 32, 1)
    F.rug(bed, 176, 100, 64, 40, 'carpet', 2)
    F.mat(hall, 76, 132, 72, 40, 3); F.mat(hall, 268, 132, 72, 40, 4)
    F.rug(work, 160, 112, 96, 44, 'lapis', 5, edge='pale')
    F.line(loft, 208, 68, 176)
    F.rug(tax, 176, 92, 64, 52, 'carpet', 6)
    F.rug(ummi, 160, 84, 112, 64, 'carpet', 7); F.mat(ummi, 300, 136, 72, 32, 8)
    F.rug(seen, 56, 104, 112, 48, 'lapis', 9, edge='gold')
    F.mat(goat, 136, 120, 56, 32, 10)
    F.mat(pots, 244, 110, 72, 40, 11)
    F.platform(nets, 96, 48, 320, 88, h=16, steps=[(232, 272)], run=16)
    F.bake()
    m = F.m

    # ================================================================ what stands in them
    # ---- the bakery shop
    F.put("in_counter_48", hin.counter(3.0, 0.6, seed=2, plaster=2), shop, 120, 132, box=(0, -10, 48, 0))
    F.put("in_table_bread", hin.table(1.4, 0.8, things='bread', seed=1), shop, 122, 168, box=(0, -13, 22, 0))
    F.put("in_table_dough", hin.table(1.5, 0.9, things='dough', seed=2), shop, 238, 104, box=(0, -14, 24, 0))
    F.put("oven", town.oven, shop, 284, 132, box=(-14, -22, 14, 0), frames=3)
    F.put("in_jars_2", hin.big_jars(2, 1), shop, 124, 92, box=(-6, -8, 16, 0))
    F.put("lt_sacks", town.sacks(40), shop, 288, 170)
    F.put("in_basket_bread", hin.basket(1, 'bread'), shop, 172, 104, box=(-4, -5, 4, 0))
    F.put("in_flour_bin", hin.flour_bin(1), shop, 256, 160, box=(-8, -12, 8, 0), kind="block", data={"id": "bk_bin"})
    F.hatch(shop, 256, 160, "bk_hatch", NAME, "bk_cellar_in", "bk_shop_dn", w=20, d=14)
    F.who(shop, 144, 118, "urbau")
    F.lights(shop)
    # ---- the bedroom over it
    F.put("in_bed_gran", hin.bed_h(1, 'red'), bed, 132, 92, box=(0, -14, 35, 0))
    F.put("in_bed_blue", hin.bed(2, 'blue', made=False), bed, 264, 94, box=(0, -30, 16, 0))
    F.put("in_cradle", hin.cradle(1), bed, 240, 112, box=(0, -8, 14, 0))
    F.put("in_water", hin.water_stand(1), bed, 164, 70, box=(-4, -5, 4, 0))
    F.put("in_lampstand", hin.lamp_stand, bed, 248, 70, box=(-3, -4, 3, 0), frames=2)
    F.chest(bed, 148, 148, "lt_bk_bed", "shekels:15")
    F.hatch(bed, 262, 146, "bk_bed_hatch", NAME, "bk_shop_up", "bk_bed_dn", w=24, d=18)
    F.who(bed, 150, 87, "granny")
    F.who(bed, 272, 80, "cat_bed")
    F.lights(bed)
    # ---- the flour cellar
    F.put("lt_sacks", town.sacks(40), cellar, 152, 100); F.put("lt_sacks_b", town.sacks(41), cellar, 160, 138)
    F.put("in_jars_3", hin.big_jars(3, 1), cellar, 236, 96, box=(-6, -8, 26, 0))
    F.put("in_basket_onions", hin.basket(2, 'onions'), cellar, 250, 138, box=(-4, -5, 4, 0))
    F.chest(cellar, 208, 132, "lt_bk_cellar", "shekels:30")
    F.say("in_stool_guard", hin.stool(3), cellar, 184, 118, (-3, -4, 3, 0),
          "A stool, down here in the dark, facing the flour.^Somebody sits and guards it. From the look of the flour, he sleeps on duty.")
    F.lights(cellar)
    # ---- the hall of the Seven Jars
    F.put("in_counter_96", hin.counter(6.0, 0.6, seed=4, plaster=4), hall, 72, 102, box=(0, -10, 96, 0))
    F.put("in_jars_straw", hin.big_jars(4, 3, straws=True), hall, 80, 84, box=None)
    F.put("in_jars_3s", hin.big_jars(3, 5, straws=True), hall, 300, 92, box=(-6, -8, 26, 0))
    for k, (x, y) in enumerate(((88, 152), (280, 152))):
        F.put("in_table_cups", hin.table(1.6, 0.9, things='cups', seed=3), hall, x, y, box=(0, -14, 26, 0))
        F.put("in_stool", hin.stool(1), hall, x - 8, y - 2, box=(-3, -4, 3, 0))
        F.put("in_stool", hin.stool(1), hall, x + 34, y - 2, box=(-3, -4, 3, 0))
    F.put("bench_1", hkit.bench(1.5, 1), hall, 76, 172, box=(0, -6, 24, 0)); F.put("bench_1", hkit.bench(1.5, 1), hall, 312, 172, box=(0, -6, 24, 0))
    F.hatch(hall, 188, 94, "beer_hatch", NAME, "beer_cellar_top", "beer_hall_dn", when="flag:beer_cellar_seen",
            say="A board in the floor behind the counter lifts.^It was bolted from underneath. Now it is not.", w=20, d=14)
    F.put("in_hearth", hin.hearth, hall, 208, 128, box=(-7, -10, 7, -2), frames=3)
    F.who(hall, 150, 88, "alewife"); F.who(hall, 96, 166, "drinker_a"); F.who(hall, 318, 150, "drinker_b"); F.who(hall, 236, 136, "dog_beer")
    F.lights(hall)
    # ---- under the Seven Jars
    for k, x in enumerate(range(124, 180, 16)):
        F.pot(under, x, 96, True); F.pot(under, x, 114, k % 2 == 0)
    F.put("in_jars_3", hin.big_jars(3, 5), under, 124, 152, box=(-6, -8, 26, 0))
    F.chest(under, 288, 140, "lt_beer_cellar", "shekels:50")
    X, Y = under.p(276, NW)
    m.model("burrow_mouth", dkit.burrow_mouth(), X, Y + 1, box=None, shadow=False, lights=False)
    m.exit(X - 8, Y - 8, X + 8, Y, "cliffs", "beer_cave")
    m.spawn("beer_cave_in", X, Y + 12, "down")
    F.enemy(under, "crab", 170, 140, "lt_cellar_c1"); F.enemy(under, "crab", 250, 124, "lt_cellar_c2")
    F.lights(under)
    # ---- the pottery
    for j, y in enumerate((100, 120, 140)):
        for i, x in enumerate(range(172, 232, 16)):
            F.pot(pots, x, y, (i + j) % 3 == 0)
    F.put("in_rack_jars", hin.rack(1.6, 'jars', 2), pots, 340, 92, box=(0, -7, 26, 0))
    F.put("wheel", town.potters_wheel(), pots, 268, 128, box=(-6, -8, 6, 0))
    F.put("in_stool", hin.stool(1), pots, 286, 130, box=(-3, -4, 3, 0))
    F.put("in_counter_48", hin.counter(3.0, 0.6, seed=2, plaster=2), pots, 316, 172, box=(0, -10, 48, 0))
    F.put("in_water", hin.water_stand(1), pots, 300, 104, box=(-4, -5, 4, 0))
    F.put("in_basket", hin.basket(4), pots, 176, 168, box=(-4, -5, 4, 0))
    F.who(pots, 296, 146, "potboy")
    F.lights(pots)
    # ---- the cash room
    F.put("in_table_coins", hin.table(1.6, 0.9, things='coins', seed=5), cash, 56, 132, box=(0, -14, 26, 0))
    F.put("in_money", hin.money_pile(1), cash, 36, 164, box=(-6, -8, 6, 0)); F.put("in_money_b", hin.money_pile(2), cash, 120, 168, box=(-6, -8, 6, 0))
    F.put("in_money", hin.money_pile(1), cash, 150, 126, box=(-6, -8, 6, 0))
    F.put("in_stool", hin.stool(1), cash, 92, 134, box=(-3, -4, 3, 0))
    F.chest(cash, 216, 150, "lt_pt_cash", "shekels:60")
    F.say("in_tally", hin.rack(1.3, 'tablets', 4), cash, 100, 94, (0, -7, 21, 0),
          "Kesh's tallies. One tablet for every pot he has ever sold, and three for every pot he has not.^The last one says: DOOR. BRICK. TOMORROW.")
    F.lights(cash)
    # ---- the weavers'
    F.put("in_loom_red", hin.loom(1, ('red', 'cream'), 0.5), work, 88, 108, box=(0, -5, 24, 0))
    F.put("in_loom_blue", hin.loom(2, ('blue', 'linen'), 0.5), work, 304, 108, box=(0, -5, 24, 0))
    F.put("in_rack_cloth", hin.rack(1.6, 'cloth', 3), work, 136, 92, box=(0, -7, 26, 0))
    F.put("in_rack_cloth_b", hin.rack(1.6, 'cloth', 5), work, 252, 92, box=(0, -7, 26, 0))
    F.put("in_tub_red", _tub('red'), work, 100, 170, box=(-7, -8, 7, 0))
    F.put("in_tub_blue", _tub('lapis'), work, 316, 170, box=(-7, -8, 7, 0))
    F.put("in_bolts", hin.cloth_bolts(1, 5), work, 180, 172, box=(-2, -12, 28, 0))
    F.put("in_basket_wool", hin.basket(1, 'wool'), work, 140, 168, box=(-4, -5, 4, 0)); F.put("in_basket_wool", hin.basket(1, 'wool'), work, 276, 168, box=(-4, -5, 4, 0))
    F.who(work, 100, 124, "sister_a"); F.who(work, 316, 124, "sister_b")
    F.lights(work)
    # ---- the sisters' room
    F.put("in_bed_red", hin.bed(1, 'red'), loft, 136, 112, box=(0, -30, 16, 0))
    F.put("in_bed_blue", hin.bed(2, 'blue', made=False), loft, 264, 112, box=(0, -30, 16, 0))
    F.put("in_water", hin.water_stand(1), loft, 176, 86, box=(-4, -5, 4, 0)); F.put("in_water", hin.water_stand(1), loft, 240, 86, box=(-4, -5, 4, 0))
    F.hatch(loft, 160, 160, "wv_hatch", NAME, "wv_work_up", "wv_upper_dn", w=24, d=18)
    F.chest(loft, 256, 160, "lt_wv_loft", "shekels:25")
    F.say("in_stool_line", hin.stool(2), loft, 208, 130, (-3, -4, 3, 0),
          "A stool, exactly on the line.^It belongs to both of them. Neither has sat on it in nine years, in case.")
    F.lights(loft)
    # ---- the goat's house
    F.put("in_chewed", hin.chewed_table(1), goat, 140, 108, box=(0, -12, 21, 0))
    F.put("in_bed_goat", hin.bed(5, 'green', made=False), goat, 264, 100, box=(0, -30, 16, 0))
    F.chest(goat, 264, 148, "lt_goat_key", "key")
    F.bar(goat, "lt_goat_latch", say="Two planks, in iron hooks. They lift out.^Whoever barred this door did it from in here, and then left by the roof. Nobody in Ashkel does that but the cats, and one other.")
    F.say("in_goat_cushion", hin.cushion('green', 3), goat, 164, 140, (-4, -5, 4, 0),
          "A cushion, in the exact middle of the mat, with a dent in it the shape of something that sleeps standing up.^It is still warm.")
    F.put("in_basket", hin.basket(4), goat, 140, 150, box=(-4, -5, 4, 0))
    F.lights(goat)
    # ---- the counting house
    F.put("in_table_scales", hin.table(1.6, 0.9, things='scales', seed=7), tax, 194, 122, box=(0, -14, 26, 0))
    F.put("in_table_tablets", hin.table(1.6, 0.9, things='tablets', seed=8), tax, 290, 146, box=(0, -14, 26, 0))
    F.put("in_rack_tablets", hin.rack(1.6, 'tablets', 6), tax, 124, 92, box=(0, -7, 26, 0))
    F.put("in_stool", hin.stool(1), tax, 330, 148, box=(-3, -4, 3, 0))
    F.put("in_tabletchest", hin.tablet_chest(1), tax, 126, 160, box=(0, -9, 14, 0))
    F.put("bench_1", hkit.bench(1.5, 1), tax, 248, 172, box=(0, -6, 24, 0))
    F.put("in_lampstand", hin.lamp_stand, tax, 256, 96, box=(-3, -4, 3, 0), frames=2)
    F.who(tax, 303, 162, "clerk")
    F.say("in_goat_file", hin.rack(1.3, 'tablets', 9), tax, 336, 92, (0, -7, 21, 0),
          "A whole shelf, labelled: GOAT, THE. GRAZING FEES OWED.^Eleven years of tablets. The oldest ones have been chewed.")
    F.lights(tax)
    # ---- the strongroom
    F.chest(vault, 96, 126, "lt_tax_vault", "vessel")
    F.put("in_money", hin.money_pile(1), vault, 40, 152, box=(-6, -8, 6, 0)); F.put("in_money_b", hin.money_pile(2), vault, 148, 132, box=(-6, -8, 6, 0))
    F.put("in_money_b", hin.money_pile(2), vault, 60, 124, box=(-6, -8, 6, 0)); F.put("in_money", hin.money_pile(1), vault, 150, 168, box=(-6, -8, 6, 0))
    F.say("in_vault_shelf", hin.rack(1.3, 'tablets', 11, rows=1), vault, 110, 168, (0, -7, 21, 0),
          "One shelf is empty but for a label: GOAT, THE. PAID.^It has never held anything.")
    F.lights(vault)
    # ---- Ummi's
    F.put("in_table_bones", hin.table(1.3, 0.8, h=0.3, things='bones', seed=9), ummi, 206, 120, box=(0, -12, 21, 0))
    for k, (x, y, col) in enumerate(((184, 128, 'fig'), (248, 124, 'blue'), (216, 140, 'red'), (330, 150, 'ochre'))):
        F.put(f"in_cushion_{col}", hin.cushion(col, k), ummi, x, y, box=None)
    for k, x in enumerate((140, 292)):
        F.put("in_censer", hin.censer_stand, ummi, x, 84, box=(-4, -5, 4, 0), frames=2)
    F.put("in_bed_fig", hin.bed(7, 'fig'), ummi, 340, 100, box=(0, -30, 16, 0))
    F.put("in_basket", hin.basket(4), ummi, 128, 168, box=(-4, -5, 4, 0))
    F.who(ummi, 216, 160, "client")
    F.lights(ummi)
    # ---- what she sees
    F.chest(seen, 80, 124, "lt_or_dream", "shekels:40", layer=2)
    F.say("in_answers", town.stele(1.5, 2), seen, 150, 124, (-5, -5, 5, 0),
          "Her answers, written down before the questions.^The last one reads: {t}yes, but not the way you are hoping.{/}| It is not dated. They never are.", layer=2)
    F.lights(seen)
    # ---- the net loft
    F.put("in_boat", hin.boat_frame(1), nets, 108, 164, box=(0, -12, 46, 0))
    F.put("in_net_heap", hin.net_heap(1), nets, 284, 150, box=(-10, -10, 10, 0))
    F.put("in_net_heap", hin.net_heap(1), nets, 290, 80, box=(-10, -10, 10, 0))
    F.put("in_basket_fish", hin.basket(3, 'fish'), nets, 196, 170, box=(-4, -5, 4, 0)); F.put("in_basket_fish", hin.basket(3, 'fish'), nets, 212, 172, box=(-4, -5, 4, 0))
    F.chest(nets, 140, 76, "lt_net_loft", "shekels:25")
    F.who(nets, 286, 140, "oldfisher")
    F.lights(nets)
    F.save()


if __name__ == "__main__":
    build()
