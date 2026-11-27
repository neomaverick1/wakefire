"""What the weather needs on the ground: the temple's dance drum, and the stick that goes with it.
  python3 sky_props.py     (draws the item icon)"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from forge import Model, M, m_planks, m_mottle


def drum():
    """The dance drum: a barrel of red cedar as high as a man's hip, a hide laced over the top, on three feet.
    There is a peg on the side for the stick, and nothing on the peg."""
    m = Model()
    wood = M('cedar', 4.0, m_planks(9, 'v'))
    m.part()
    for (x, y) in ((-0.26, 0.14), (0.26, 0.14), (0.0, -0.24)):
        m.box(x - 0.06, y - 0.06, 0, x + 0.06, y + 0.06, 0.14, M('cedar', 3.2), top=M('cedar', 3.8))
    m.part(); m.turned(0, 0.0, [(0.33, 0.12), (0.43, 0.34), (0.45, 0.56), (0.40, 0.80)], wood, n=14)
    m.part(); m.turned(0, 0.0, [(0.445, 0.40), (0.455, 0.46)], M('red', 3.6), n=14)
    m.part(); m.turned(0, 0.0, [(0.415, 0.76), (0.415, 0.83)], M('bronze', 4.0, m_mottle(5, 0.4), gloss=0.03), n=14)
    m.part(); m.turned(0, 0.0, [(0.40, 0.83), (0.0, 0.85)], M('linen', 4.5), n=14)
    m.part(); m.box(0.44, -0.03, 0.52, 0.54, 0.03, 0.56, M('bronze', 3.6))
    return m


def item_drumstick():
    """Kessi's drumstick: a forearm of olive wood with a wad of wool bound on one end, and the other end chewed."""
    m = Model()
    m.part(); m.limb([(-0.24, 0.2, 0.06), (0.14, 0.2, 0.42)], [0.045, 0.038], M('wood', 4.0), n=6)
    m.part(); m.blob(0.20, 0.2, 0.48, 0.15, 0.14, 0.15, M('linen', 4.8, soft=True), n=8, rings=5)
    m.part(); m.limb([(0.09, 0.2, 0.37), (0.12, 0.2, 0.40)], [0.062, 0.062], M('red', 3.4), n=6)
    return m


if __name__ == '__main__':
    import necro_items
    necro_items.icon('drumstick', item_drumstick())
