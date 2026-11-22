// Chapter two: the Sleepless Dead. All the sleep in the world ran downhill to the living, so on
// the Hill of Sleepers the dead are awake, and have been for forty nights, and are being very
// polite about it. Here: how the chapter opens on the summit, the gate on the terraces, the
// road of the dead and its queue, the hilltop and the three stones that spell a king's name,
// the three halls of his tomb, Kurashtar himself (who has waited up four hundred years to be
// woken), the Dawn Horn, and the one breath of morning it buys.
//
// The rule of the place: the dead do not dream. Whatever they are doing in the waking world,
// in the dream they are simply not there.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        Map hillMap;

        // ------------------------------------------------------------------ how it starts
        /// <summary>On the summit, the bull broken and the god still asleep: what next. Runs straight
        /// on from the end of chapter one, or when a finished game is picked up again.</summary>
        public IEnumerator ChapterTwoOpens(Npc ebrumSelf = null, Npc goatHere = null)
        {
            var p = Player.I;
            Set("ch2");
            Fade.Set(1);
            Music.Play("summit");
            yield return Card("CHAPTER TWO", "THE SLEEPLESS DEAD");
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            p.SetState(Player.State.Cutscene, "idle");
            if (ebrum)
            {
                // beside the altar, where a man would stand to ask a sleeping priest a question
                foreach (var off in new[] { new Vector2(-1.5f, -1.1f), new Vector2(1.5f, -1.1f), new Vector2(0, -1.8f), new Vector2(-2.2f, 0) })
                {
                    var at = ebrum.pos + off;
                    if (Solids.Overlaps(new Rect(at - p.half, p.half * 2), at, p)) continue;
                    p.pos = at;
                    break;
                }
                p.Face(ebrum.pos.x > p.pos.x ? Facing.Right : Facing.Left);
                PixelView.I.SnapTo(p.pos);
            }
            yield return Fade.In(1.0f);
            yield return Wait(0.4f);
            yield return AzarSays("Right.| So how do you wake a god?");
            yield return Wait(0.7f);
            yield return Narrate("Nobody answers. Everyone who would know is asleep.");
            yield return AzarSays("...Fine. I'll come to you.");
            p.SetState(Player.State.Cutscene, "nod");
            yield return Wait(0.5f);
            Dream.I.Drowsiness = 1;
            Dream.I.Seconds = 9999;
            Sfx.Play("dream_in");
            Dream.I.Flip(p.pos, true);
            yield return Wait(1.1f);
            var self = ebrumSelf;
            if (!self && ebrum) self = Npc.Create("ebrum_self", ebrum.pos + new Vector2(1.2f, 0), "priest", "idle", WorldLayer.Dream, Facing.Down, false);
            yield return Say("Ebrum", "Back again? I had only just got comfortable.", "priest", true);
            yield return AzarSays("How do you wake him?");
            yield return Say("Ebrum", "You don't. Nobody ever has. For a thousand years the {g}Dawn Horn{/} did it.", "priest", true);
            yield return Say("Ebrum", "One note at sunrise, and up he'd get. Grumbling. But up.", "priest", true);
            yield return AzarSays("Where is it?");
            yield return Say("Ebrum", "King Kurashtar had it buried with him. Four hundred years ago.", "priest", true);
            yield return Say("Ebrum", "He said if he wasn't getting any more mornings, he would like to be told when one happened.", "priest", true);
            yield return AzarSays("And for the four hundred years since?");
            yield return Say("Ebrum", "A rooster.| The rooster is asleep.", "priest", true);
            yield return Say("Ebrum", "The king lies on the {g}Hill of Sleepers{/}, above the olive terraces. The temple keeps the key to the gate.| It's on my belt.", "priest", true);
            yield return Narrate("You reach for the High Priest's belt.");
            yield return Say("Ebrum", "Other side.| ...I'm lying on it. Sorry.", "priest", true);
            Sfx.Play("dream_out");
            Dream.I.Flip(p.pos, false);
            p.SetState(Player.State.Cutscene, "wake");
            yield return Wait(1.1f);
            Dream.I.SetInstant(false);
            ApplyItems();
            Set("item_hillkey");
            yield return ItemGet("hill_key", "You got the {g}HILL KEY{/}!^It has been under a priest for forty nights. It is very warm.");
            yield return Say("Ebrum", "Be polite...| up there...| they've been dead a long time...| they're particular about it...", "priest");
            Sfx.Play("goat");
            yield return Wait(0.7f);
            p.SetState(Player.State.Cutscene, "idle");
            yield return Fade.Out(1.0f);
            if (self) Destroy(self.gameObject);
            if (goatHere) Destroy(goatHere.gameObject);
            yield return Card("Four hundred steps down.", "The goat was at the bottom first.\nIt always is.");
            Game.I.EnterMap("terraces", "hill");
            Save.Write("terraces", "hill");
            Notices.Place("terraces");
            p.SetState(Player.State.Talk, "idle");
            yield return Fade.In(0.8f);
        }

        IEnumerator AfterTheBull()
        {
            // a finished game picked up again: give the room a moment to come up, then go on with the story
            yield return null;
            while (Running || Game.Busy || Fade.Amount > 0.05f || Title.I) yield return null;
            yield return Wait(0.4f);
            if (Map.Current && Game.I.CurrentMap == "zig_3")
            {
                if (Has("item_horn") && !Has("chapter2_done")) Run(Dawn());
                else if (!Has("ch2")) Run(ChapterTwoOpens());
            }
        }

        // ------------------------------------------------------------------ the gate on the terraces
        IEnumerator HillGate(Prop gate)
        {
            if (Has("hill_gate")) { yield return Narrate("The gate stands open. Cold air comes down the steps."); yield break; }
            if (!Has("item_hillkey"))
            {
                yield return Narrate("The gate to the {g}Hill of Sleepers{/}. Barred, chained and bolted from this side.^Whoever locked it was not worried about anyone getting in.");
                yield break;
            }
            yield return Narrate("The Hill Key turns. It has not turned in a long time, and says so.");
            Sfx.Play("gate_open", 1f, 0f);
            PixelView.I.Shake(2, 0.6f);
            Set("hill_gate");
            SwingOpen(gate, "hill_gate_open");
            Fx.Dust(gate.basePos + new Vector2(0, -0.2f), 8);
            yield return Wait(0.8f);
            yield return Narrate("Cold air comes down the steps. It smells of dust, lamp oil, and a very long wait.");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        /// <summary>A gate that stays where it is but stands open: its open picture, and no wall.</summary>
        void SwingOpen(Prop gate, string openSprite)
        {
            if (!gate) return;
            if (gate.solid != null) { Solids.Remove(gate.solid); gate.solid = null; }
            foreach (var o in Map.Current.data.objects)
                if (o.s == openSprite) { gate.data.px = o.px; gate.data.py = o.py; gate.SetSprite(o.s, o.px, o.py); }
        }

        // ------------------------------------------------------------------ who is on the hill
        /// <summary>After the dawn the dead are asleep: nobody stands in the gap or across the hall.</summary>
        static void Unblock(float x0, float y0, float x1, float y1)
        {
            var a = Map.ToWorld(x0, y1);
            var r = new Rect(a.x + 0.05f, a.y + 0.05f, (x1 - x0) / 16f - 0.1f, (y1 - y0) / 16f - 0.1f);
            foreach (var s in Solids.All) if (s.layer == WorldLayer.Waking && !s.pit && s.r.Overlaps(r)) s.enabled = false;
        }

        readonly System.Collections.Generic.List<Vector2> graves = new System.Collections.Generic.List<Vector2>();
        float graveClock;

        void SetupHill(string map, Map m)
        {
            hillMap = m;
            king = null;
            graves.Clear();
            bool asleep = Has("chapter2_done");
            foreach (var mk in m.data.markers)
                if (mk.kind == "npc") SpawnHill(mk.who, Map.ToWorld(mk.x, mk.y), asleep);
            propHandler = HillProp;
            if (asleep)
            {
                // every door on the hill has somebody snoring behind it
                foreach (var pr in m.props)
                    if (pr && pr.data.s != null && (pr.data.s.StartsWith("tomb_") || pr.data.s.StartsWith("tumulus_") || pr.data.s.StartsWith("grave_")))
                        graves.Add(pr.basePos + new Vector2(0, pr.data.s.StartsWith("grave_") ? 0.9f : 1.4f));
                if (map == "necro_road") Unblock(394, 286, 446, 300);
                if (map == "tomb_1") Unblock(428, 290, 468, 302);
            }
            switch (map)
            {
                case "necropolis":
                    if (Has("name_tar")) foreach (var id in new[] { "garden_0", "garden_1" }) { var b = m.Find(id); if (b) b.Ignite(); }
                    if (Has("king_door")) SwingOpen(m.Find("king_door"), "king_door_open");
                    break;
                case "tomb_2":
                    if (Has("door_t2_seal"))
                    {
                        for (int i = 0; i < 4; i++) { var b = m.Find("lyre_" + i); if (b) b.Ignite(); }
                        var d = m.Find("t2_seal");
                        if (d) d.Open();
                    }
                    break;
                case "tomb_3": StartCoroutine(SetupThrone(m)); break;
            }
        }

        /// <summary>One of the dead: seen through, awake, and absent from every dream.</summary>
        Npc Dead(string id, Vector2 at, string look, string anim, string voice, System.Func<IEnumerator> talk, Facing f = Facing.Down, bool solid = true)
        {
            var n = Npc.Create(id, at, "priest", anim, WorldLayer.Waking, f, solid, look);
            n.voice = voice;
            n.talk = talk;
            return n.Ghost();
        }

        /// <summary>A living thief, asleep where the sleep caught him, and the self he dreams.</summary>
        void Robber(string id, Vector2 at, string look, System.Func<IEnumerator> wake, System.Func<IEnumerator> dream, Vector2 selfOff)
        {
            var body = Npc.Create(id, at, "priest", "lie", WorldLayer.Waking, Facing.Down, true, look);
            body.turnsToTalk = false;
            body.talk = wake;
            var self = Npc.Create(id + "_self", at + selfOff, "priest", "idle", WorldLayer.Dream, Facing.Down, false, look);
            self.voice = "robber";
            self.talk = dream;
        }

        void SpawnHill(string who, Vector2 at, bool asleep)
        {
            // once the dawn has come and gone the dead are in their beds; only the living and the goat are about
            if (asleep && !who.StartsWith("goat") && !who.StartsWith("robber")) return;
            switch (who)
            {
                // ---- the road
                case "namtar":
                {
                    var n = Dead("namtar", at, "namtar", "wait", "clerk", TalkNamtar, Facing.Left);
                    if (!Has("met_namtar")) n.notice = TalkNamtar;
                    break;
                }
                case "gran_dur": Dead("gran_dur", at, "gran", "idle", "ghost_old", TalkGran); break;
                case "belu": Dead("belu", at, "belu", "idle", "ghost", TalkBelu, Facing.Left); break;
                case "queue_0": Dead(who, at, "dead_baker", "wait", "ghost_f", () => TalkQueue(0), Facing.Up).turnsToTalk = false; break;
                case "queue_1": Dead(who, at, "dead_fisher", "wait", "ghost", () => TalkQueue(1), Facing.Up).turnsToTalk = false; break;
                case "queue_2": Dead(who, at, "dead_potter", "wait", "ghost", () => TalkQueue(2), Facing.Up).turnsToTalk = false; break;
                case "queue_3": Dead(who, at, "dead_sleeper", "wait", "ghost", () => TalkQueue(3), Facing.Up).turnsToTalk = false; break;
                case "goat_tomb":
                    GoatCameo(at, "The goat is standing on a tomb.^The dead don't mind. It is the only visitor they have had in forty years who didn't want something.", Facing.Left);
                    break;
                // ---- the hilltop
                case "general_a": Dead(who, at, "general_a", "sit", "general", TalkGenerals, Facing.Right, false).turnsToTalk = false; break;
                case "general_b": Dead(who, at, "general_b", "sit", "general", TalkGenerals, Facing.Left, false).turnsToTalk = false; break;
                case "poet": Dead(who, at, "poet", "idle", "ghost", TalkPoet); break;
                case "doorman": Dead(who, at, "herald", "lamp", "clerk", TalkHerald, Facing.Right); break;
                case "goat_hill":
                    GoatCameo(at, "The goat got to the top of the Hill of Sleepers before you did.^It is eating an offering. Nobody here is in a position to object.", Facing.Right);
                    break;
                // ---- the tomb
                case "robber_a":
                    Robber(who, at, "robber", () => One(Narrate("A tomb robber, asleep on a sack of somebody else's gold.^Alive. Snoring. Forty nights into the job.")), TalkZimu, new Vector2(0.4f, -0.9f));
                    break;
                case "robber_b":
                    Robber(who, at, "robber_b", () => One(Narrate("Another one, face down in a heap of cups. He is smiling.")), TalkKuri, new Vector2(0.9f, -0.5f));
                    break;
                case "robber_c":
                    Robber(who, at, "robber", () => One(Narrate("A third robber, asleep with both arms round the foot of a golden lyre that is not his.")), TalkLyreThief, new Vector2(-0.9f, 0.3f));
                    break;
                case "robber_d":
                    Robber(who, at, "robber_b", () => One(Narrate("A fourth. He got all the way to the king's own chamber before the sleep took him.^Whatever else he is, he is thorough.")), TalkLastThief, new Vector2(0.7f, 0.5f));
                    break;
                default:
                    if (who.StartsWith("servant_"))
                    {
                        var n = Dead(who, at, "servant", "wait", "ghost", TalkServants, Facing.Down, false);
                        n.turnsToTalk = false;
                    }
                    break;
            }
        }

        // ------------------------------------------------------------------ the road of the dead
        IEnumerator TalkNamtar()
        {
            const string who = "Namtar";
            int n = Bump("namtar");
            if (n == 0)
            {
                Set("met_namtar");
                yield return Say(who, "Name.", "clerk");
                yield return AzarSays("Azar. Night watch.");
                yield return Say(who, "Date of death.", "clerk");
                yield return AzarSays("I'm not dead.");
                yield return Say(who, "...Then you want the other form.", "clerk");
                yield return Say(who, "There is no other form.", "clerk");
                yield return Say(who, "Four hundred years I have kept this gate, and nobody has ever come through it warm. I shall have to make something up.", "clerk");
                yield return AzarSays("Why is everyone up here awake?");
                yield return Say(who, "Forty nights ago every bit of sleep in the world ran downhill to the living. We woke up. All of us. After four hundred years of the best sleep anyone ever had.", "clerk");
                yield return Say(who, "The dead do not get tired, watchman. We cannot even look forward to it.", "clerk");
                yield return AzarSays("I'm here for the Dawn Horn. King Kurashtar has it.");
                yield return Say(who, "Top of the hill. He never went to sleep in the first place. He is waiting to be woken.| He takes it very seriously.", "clerk");
                yield return Say(who, "His door opens to his name. All of it. It is cut on {g}three stones{/}, the lowest first, because a king cannot say anything once.", "clerk");
                yield return Say(who, "And there is a queue.", "clerk");
            }
            else if (n == 1)
            {
                yield return Say(who, "Three stones. One on this road, two on the hilltop. And the queue.", "clerk");
                yield return Say(who, "You cannot push in. You could {t}dream{/} of pushing in, I suppose. We could not stop you.| The dead do not dream. It is one of the things we miss.", "clerk");
            }
            else yield return Say(who, "I have put you down as 'visitor, warm'. It is the first new box on the form in four hundred years.| I am quite pleased with it.", "clerk");
        }

        IEnumerator TalkQueue(int i)
        {
            switch (i)
            {
                case 0:
                    yield return Say("Front of the Queue", Bump("queue0") == 0
                        ? "Forty nights at the front. I keep hoping you are the man who lets us through.| He is back there. Talking to you."
                        : "It is no use asking me to step aside. I am dead. I have all the time there is and I mean to spend it right here.", "ghost_f");
                    break;
                case 1:
                    yield return Say("Second in the Queue", "Three hundred years dead and never once kept waiting.| Now look.", "ghost");
                    break;
                case 2:
                    yield return Say("Third in the Queue", "Don't push.| There is nowhere to go. That is not the point. Don't push.", "ghost");
                    break;
                default:
                    yield return Say("Back of the Queue", "Is this the queue for sleep?| No?| I'll stay anyway. I've started.", "ghost");
                    break;
            }
        }

        IEnumerator QueuePassed()
        {
            Set("queue_passed");
            yield return Wait(0.3f);
            yield return Say("Front of the Queue", "Did he just...", "ghost_f");
            yield return Say("Back of the Queue", "He dreamed past us.| Can he do that?", "ghost");
            yield return Say("Front of the Queue", "Somebody write that down.", "ghost_f");
        }

        IEnumerator TalkGran()
        {
            const string who = "Great-Grandmother Dur";
            if (Bump("gran") == 0)
            {
                yield return Say(who, "You're from the Gate. I can tell by the helmet. Is a Dur still captain?", "ghost_old");
                yield return AzarSays("Captain Dur. Asleep on his feet. Forty nights.");
                yield return Say(who, "On his feet! That's my blood. I died standing up, you know.| Out of spite.", "ghost_old");
                yield return Say(who, "Does he still think the dark has teeth?", "ghost_old");
                yield return AzarSays("...He might.");
                yield return Say(who, "I made that up. To get my boy in for his supper. Three hundred years, and they are still handing it down.", "ghost_old");
                yield return Say(who, "Tell him the dark has nothing in it. I've looked.", "ghost_old");
            }
            else yield return Say(who, "If you get the sleep back, don't wake me for anything.| Not even a fire.| Especially not a fire.", "ghost_old");
        }

        IEnumerator TalkBelu()
        {
            const string who = "Old Belu";
            if (Has("figs_given"))
            {
                yield return Say(who, "She ate one? She did.| She said they were good?| She didn't say. No. She wouldn't.", "ghost");
                yield break;
            }
            if (Has("item_figs"))
            {
                yield return Say(who, "She'll have words. Several. I have had forty years to work out my side of it, and I have nothing.", "ghost");
                yield break;
            }
            yield return Say(who, "Figs?", "ghost");
            yield return AzarSays("...Are you Widow Ilta's husband?");
            yield return Say(who, "You know my wife! How is she?", "ghost");
            yield return AzarSays("She says you went out for figs. Forty years ago.");
            yield return Say(who, "I did. I got them, too. Then I sat down on the hill road for one moment, and here we are.", "ghost");
            yield return Say(who, "I can't go down. The dead don't leave the hill. Would you take them to her?", "ghost");
            Set("item_figs");
            yield return ItemGet("figs", "You got {g}BELU'S FIGS{/}!^Forty years old and still soft. Nobody is going to ask how.");
            yield return Say(who, "Tell her they were worth it.| No.| Don't tell her that.", "ghost");
            yield return Narrate("Widow Ilta walks her round by the {g}Temple Gate{/}. She will want these in a dream, where she can say what she thinks.");
        }

        /// <summary>The widow gets her figs, forty years late (called from her own talk in the square).</summary>
        IEnumerator FigsDelivered()
        {
            Set("figs_given");
            yield return Say("Widow Ilta", "Figs.| These are his figs.| Where did you...", "woman", true);
            yield return AzarSays("He sat down on the hill road for a moment. He says he's sorry.");
            yield return Say("Widow Ilta", "Forty years.| For figs.", "woman", true);
            yield return Wait(0.6f);
            yield return Say("Widow Ilta", "...They are very good figs.| Don't you dare tell him.", "woman", true);
            yield return Say("Widow Ilta", "Here. I was keeping this for when he came home. You have it.", "woman", true);
            yield return GiveItem("vessel");
        }

        // ------------------------------------------------------------------ the three stones
        int NameParts => (Has("name_kur") ? 1 : 0) + (Has("name_ash") ? 1 : 0) + (Has("name_tar") ? 1 : 0);

        IEnumerator ReadStone(string part, string first, string again)
        {
            if (Has("name_" + part)) { yield return Narrate(again); yield break; }
            Set("name_" + part);
            Sfx.Play("secret", 1f, 0f);
            yield return Narrate(first);
            int n = NameParts;
            yield return Narrate(n == 3 ? "That is all three. The king's door is at the top of the hill." : n == 2 ? "Two parts of a king's name. One to find." : "One part of a king's name. Two to find.");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        bool GardenLit()
        {
            var a = hillMap ? hillMap.Find("garden_0") : null;
            var b = hillMap ? hillMap.Find("garden_1") : null;
            return a && b && a.lit && b.lit;
        }

        // ------------------------------------------------------------------ the hilltop
        IEnumerator TalkGenerals()
        {
            const string a = "General Ushur", b = "General Baltu";
            int n = Bump("generals");
            if (n == 0)
            {
                yield return Say(a, "It's his move.", "general");
                yield return Say(b, "It has been my move for three hundred and ninety-one years. I am thinking.", "general");
                yield return AzarSays("What happened to you two?");
                yield return Say(a, "We killed each other. Same battle. Same moment.", "general");
                yield return Say(b, "It is the only thing we have ever agreed on.", "general");
                yield return Say(a, "You want the king? His name is on three stones. One on the road, one on the rock in the split, one in the old garden.", "general");
                yield return Say(b, "You won't read the garden one. Nobody has lit the altars since the gardener died.", "general");
                yield return Say(a, "The gardener is fine. He is right over there. He says it isn't his job any more.", "general");
            }
            else if (n == 1)
            {
                yield return Say(b, "Don't tell me.| Don't tell me.| ...Is it the piece on the left?", "general");
                yield return Say(a, "I am not telling you.", "general");
            }
            else yield return Say(a, "Road. Rock. Garden. Lowest first.| And take your time. He has.", "general");
        }

        IEnumerator TalkPoet()
        {
            const string who = "Imdi the Poet";
            int n = Bump("poet");
            if (n == 0)
            {
                yield return Say(who, "'Here lies Imdi, who wrote...'| No.", "ghost");
                yield return Say(who, "'Here rests Imdi...'| I am not resting, am I. That is the whole problem.", "ghost");
                yield return AzarSays("You're writing your own epitaph?");
                yield return Say(who, "For four hundred years. I had it, once. Then I woke up and it wasn't true any more.", "ghost");
                yield return Say(who, "You're after the king's name? It climbs the hill, like everything else here. Start at the bottom.", "ghost");
                yield return Say(who, "It doesn't scan. I told him so.| That is why I am buried downwind.", "ghost");
            }
            else if (n == 1)
            {
                yield return Say(who, "'Here waits Imdi.'", "ghost");
                yield return Say(who, "...Oh.| Oh, that's it.| That's terrible. That's it.", "ghost");
            }
            else yield return Say(who, "'Here waits Imdi.' Two words and a name. Four hundred years.| Don't tell the others how long it took.", "ghost");
        }

        IEnumerator TalkHerald()
        {
            const string who = "The King's Herald";
            if (Has("king_door"))
            {
                yield return Say(who, "I ought to have announced you.| I have forgotten how it goes. It starts with a trumpet. I haven't got one.", "clerk");
                yield break;
            }
            if (NameParts == 3)
            {
                yield return Say(who, "You have it? All three parts?| Then say it to the door. Not to me. I would only have to announce you.", "clerk");
                yield break;
            }
            if (Bump("herald") == 0)
            {
                yield return Say(who, "The king is not receiving.", "clerk");
                yield return AzarSays("When does he receive?");
                yield return Say(who, "He has not received in four hundred years.| But today especially.", "clerk");
                yield return Say(who, "The door opens to his name, spoken in full and in order. I would tell you, but I am paid not to.", "clerk");
                yield return Say(who, "I was paid once. In advance. I have been making it last.", "clerk");
            }
            else yield return Say(who, "His name, in full, in order. Three stones. I have said too much. I have said exactly what I am paid to say.", "clerk");
        }

        IEnumerator KingsDoor(Prop door)
        {
            if (Has("king_door")) { yield return Narrate("The door of the tomb stands open on the dark."); yield break; }
            int n = NameParts;
            if (n < 3)
            {
                yield return Narrate("A door of black stone, shut for four hundred years. No keyhole. No handle.^It wants a name." +
                                     (n == 0 ? " You have none of its three parts." : n == 1 ? " You have one of its three parts." : " You have two of its three parts."));
                yield break;
            }
            yield return Narrate("The door wants a name. All of it, in order.");
            yield return DialogueBox.Ask(null, "The first part:", "KUR", "TAR");
            bool right = DialogueBox.Choice == 0;
            yield return DialogueBox.Ask(null, "The second:", "TAR", "ASH");
            right &= DialogueBox.Choice == 1;
            yield return DialogueBox.Ask(null, "The last:", "ASH", "TAR");
            right &= DialogueBox.Choice == 1;
            if (!right)
            {
                Sfx.Play("deny");
                yield return Narrate(Bump("door_wrong") == 0 ? "Nothing.^Inside, a very long way off, somebody sighs."
                                                             : "Nothing.^They say the name climbs the hill: the lowest stone first, the highest last.");
                yield break;
            }
            yield return AzarSays("Kur. Ash. Tar.| Kurashtar.");
            Sfx.Play("stone_door", 1f, 0f);
            PixelView.I.Shake(2, 2.2f);
            yield return Wait(1.6f);
            Set("king_door");
            SwingOpen(door, "king_door_open");
            Fx.Dust(door.basePos + new Vector2(-1.2f, 0.1f), 8);
            Fx.Dust(door.basePos + new Vector2(1.2f, 0.1f), 8);
            yield return Wait(1.0f);
            yield return Narrate("Stone moves on stone. Four hundred years of dust come out to see who it is.");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        // ------------------------------------------------------------------ inside the tomb
        IEnumerator TalkServants()
        {
            yield return Narrate(Bump("servants") == 0
                ? "The king's servants, dead and on duty, shoulder to shoulder in the one doorway.^Not one of them has sat down in four hundred years. Not one of them is going to let you by."
                : "You ask them to move.^They heard. They are thinking about whether it was an order.");
        }

        IEnumerator TalkZimu()
        {
            const string who = "Zimu";
            if (Bump("zimu") == 0)
            {
                yield return Say(who, "We're rich! Look at it! Cups! Rings! A whole gold goat!", "robber", true);
                yield return AzarSays("You're asleep on the floor of a tomb.");
                yield return Say(who, "Rich AND asleep. I have had worse jobs.", "robber", true);
                yield return Say(who, "The key's through there, behind the staff. They haven't sat down in four hundred years, that lot.", "robber", true);
                yield return Say(who, "We walked straight through them in our sleep. Then we couldn't wake up to spend any of it.", "robber", true);
            }
            else yield return Say(who, "If you see a way to carry a gold goat out of a dream, I will go halves.", "robber", true);
        }

        IEnumerator TalkKuri()
        {
            const string who = "Kuri";
            if (Bump("kuri") == 0)
            {
                yield return Say(who, "Don't tell the king we're here.", "robber", true);
                yield return Say(who, "He knows. He has walked past twice. He stepped over Zimu.", "robber", true);
                yield return Say(who, "He's not angry. He's just awake.| It's worse.", "robber", true);
            }
            else yield return Say(who, "You can't hit him, you know. We tried. Goes straight through.| His crown, though. That's real. We weighed it with our eyes.", "robber", true);
        }

        IEnumerator TalkLyreThief()
        {
            const string who = "Dadu";
            if (Bump("dadu") == 0)
            {
                yield return Say(who, "Solid gold, this lyre. It's also the only thing in here that screams when you pick it up.", "robber", true);
                yield return AzarSays("Have you tried playing it?");
                yield return Say(who, "I'm a thief, not a monster.", "robber", true);
            }
            else yield return Say(who, "Four fires for the big door. It says so on the wall. I can't read, but Kuri can, and Kuri says four.", "robber", true);
        }

        IEnumerator TalkLastThief()
        {
            const string who = "Abba";
            yield return Say(who, "Psst. The crown. It's real. HE isn't, but the crown is.", "robber", true);
            yield return Say(who, "He's not here when you're asleep. None of them are. But the crown just hangs there.| I'd have it myself if I had hands in here.", "robber", true);
        }

        void SealOpens(Map m)
        {
            Set("door_t2_seal");
            Sfx.Play("secret", 1f, 0f);
            var d = m.Find("t2_seal");
            Run(SealScene(d));
        }

        IEnumerator SealScene(Prop d)
        {
            yield return Wait(0.5f);
            if (d)
            {
                yield return CamTo(d.basePos + new Vector2(0, -1.0f), 0.9f);
                Sfx.Play("gate_open", 1f, 0f);
                PixelView.I.Shake(2, 0.6f);
                yield return Wait(0.7f);
                d.Open();
                yield return Wait(0.6f);
            }
            yield return Narrate("Four fires, for the four watches of the night.^The bronze sun on the far door warms, and lets go.");
            yield return CamBack(0.7f);
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        int LyreFires()
        {
            int n = 0;
            if (!hillMap) return 0;
            for (int i = 0; i < 4; i++) { var b = hillMap.Find("lyre_" + i); if (b && b.lit) n++; }
            return n;
        }

        // ------------------------------------------------------------------ things on the hill
        void HillProp(Prop pr)
        {
            bool dream = Dream.I.IsDreamAt(pr.basePos);
            string map = Game.I.CurrentMap;
            switch (pr.Kind)
            {
                case "brazier":
                    if (!pr.lit) break;
                    if (map == "necropolis" && !Has("name_tar") && GardenLit())
                        Run(ReadStone("tar", "Firelight climbs the old stone between the two altars. One sign stands up out of the shadow:^{g}TAR{/}| 'The judge.' The highest of three.",
                                      "{g}TAR{/}: the judge. The highest of three."));
                    else if (map == "tomb_2" && !Has("door_t2_seal") && LyreFires() >= 4) SealOpens(hillMap);
                    else if (map == "tomb_2" && !Has("door_t2_seal") && Bump("lyre_first") == 0)
                        Run(Narrate("The fire takes. Somewhere in the far wall, bronze ticks as it warms.^One of four."));
                    break;
                case "gate":
                    if (pr.data.id == "king_door") Run(KingsDoor(pr));
                    else if (pr.data.id == "t2_seal")
                        Run(Narrate("A door of bronze with the sun on it, cold as the floor.^Four fire altars stand in this hall. " +
                                    (LyreFires() == 0 ? "None of them is lit." : LyreFires() == 1 ? "One of them is lit." : LyreFires() + " of them are lit.")));
                    break;
                case "pot":
                    Run(Narrate("A jar for the journey. Whoever it was packed for has not gone anywhere."));
                    break;
                case "look":
                    switch (pr.data.id)
                    {
                        case "stele_kur":
                            Run(ReadStone("kur", "An old standing stone. Most of it has worn smooth, but one sign is still cut deep:^{g}KUR{/}| 'The mountain.' The lowest of three.",
                                          "{g}KUR{/}: the mountain. The lowest of three."));
                            break;
                        case "stele_ash":
                            Run(ReadStone("ash", "A stone on a rock in the middle of nothing, where only a dreamer could come to read it:^{g}ASH{/}| 'The fire.' The middle one of three.",
                                          "{g}ASH{/}: the fire. The middle one of three."));
                            break;
                        case "stele_tar":
                            if (Has("name_tar")) Run(Narrate("{g}TAR{/}: the judge. The highest of three."));
                            else if (GardenLit())
                                Run(ReadStone("tar", "Firelight climbs the old stone between the two altars. One sign stands up out of the shadow:^{g}TAR{/}| 'The judge.' The highest of three.",
                                              "{g}TAR{/}: the judge. The highest of three."));
                            else Run(Narrate("A standing stone under the dead trees. It is too dark here to read what is cut in it.^Two fire altars stand beside it, cold."));
                            break;
                        case "game_board":
                            Run(Narrate("The game of twenty squares. One piece has not moved in three hundred and ninety-one years.^It is a good piece. You can see why he is attached to it."));
                            break;
                        case "lyre":
                            Run(Lyre());
                            break;
                        case "throne":
                            Run(Narrate(Has("king_done") ? "The king's throne. Empty, for the first time in four hundred years.^The cushion has kept his shape."
                                                         : "The throne of Kurashtar. It is occupied."));
                            break;
                    }
                    break;
            }
        }

        IEnumerator Lyre()
        {
            yield return Narrate("The queen's lyre. One string still holds.^You pluck it.");
            Sfx.Play("lyre", 1f, 0f);
            yield return Wait(1.6f);
            yield return Narrate(dreamAt(Player.I.pos)
                ? "The note goes down the hall and does not come back.^The thief asleep beside it flinches anyway."
                : "The note goes down the hall and does not come back.^On the wall behind, old writing: 'Four fires for the four watches of the night. Then he will see you.'");
        }

        static bool dreamAt(Vector2 p) => Dream.I && Dream.I.IsDreamAt(p);

        /// <summary>The parts of the hill's story that happen because of where Azar is standing.</summary>
        void HillUpdate()
        {
            var m = Map.Current;
            var p = Player.I;
            if (!m || m != hillMap || !p) return;
            if (graves.Count > 0 && !Game.Paused && (graveClock -= Time.deltaTime) <= 0)
            {
                // four hundred years of the dead, asleep at last
                graveClock = Random.Range(0.25f, 0.6f);
                var g = graves[Random.Range(0, graves.Count)];
                var v = PixelView.I;
                if (v && Mathf.Abs(g.x - v.focus.x) < 13f && Mathf.Abs(g.y - v.focus.y) < 8f) Zed.Spawn(g, WorldLayer.Waking);
            }
            if (Running || Game.Busy || p.state != Player.State.Free) return;
            if (Game.I.CurrentMap == "necro_road" && !Has("queue_passed") && p.pos.y > Map.ToWorld(0, 278).y && !dreamAt(p.pos) && !Dream.I.Dreaming)
                Run(QueuePassed());
        }

        // ------------------------------------------------------------------ the king
        SleeplessKing king;

        IEnumerator SetupThrone(Map m)
        {
            if (Has("king_done")) yield break;
            var tm = m.Marker("throne");
            king = SleeplessKing.Spawn(Map.ToWorld(tm.x, tm.y));
            // wait for Azar to come far enough in to be seen
            while (Player.I && Player.I.pos.y < Map.ToWorld(0, 330).y) yield return null;
            while (Running || Game.Busy) yield return null;
            if (king) Run(KingWakes(m));
        }

        IEnumerator KingWakes(Map m)
        {
            bool again = Has("king_seen");
            Set("king_seen");
            Music.Stop();
            var p = Player.I;
            const string who = "Kurashtar";
            if (!again)
            {
                yield return CamTo(king.pos + new Vector2(0, -1.2f), 1.6f);
                yield return Wait(0.5f);
                yield return Say(who, "IS IT MORNING.", "king");
                yield return AzarSays("No.");
                yield return Say(who, "Then why am I being disturbed.", "king");
                yield return AzarSays("You're King Kurashtar?");
                yield return Say(who, "I AM KURASHTAR. MOUNTAIN OF FIRE AND JUDGEMENT.| I chose it myself.", "king");
                yield return AzarSays("I need the Dawn Horn. The god's asleep. The whole city's asleep.");
                yield return Say(who, "I was promised I would be woken. I had the Horn buried with me so that I should hear the first morning of the next world.", "king");
                yield return Say(who, "I have waited up for it. Four hundred years. I have not so much as blinked.", "king");
                yield return AzarSays("You stayed awake...| so that you wouldn't miss being woken up.");
                yield return Say(who, "...When you say it like that it sounds foolish.", "king");
                yield return Say(who, "It is MY horn, watchman. You may not have it.", "king");
            }
            else yield return CamTo(king.pos + new Vector2(0, -1.2f), 0.8f);
            yield return king.Rise();
            PixelView.I.Shake(2, 0.5f);
            yield return Wait(0.4f);
            yield return CamBack(0.7f);
            Music.Play("king");
            king.Defeated = () => RunWhenFree(KingYields());
            king.Moment = KingMoment;
            king.Begin();
        }

        void KingMoment(string what)
        {
            switch (what)
            {
                case "pass":
                    if (Bump("king_pass") == 0)
                        Run(Narrate("Your blade goes through him like a hand through smoke.^You can't cut the dead.| But the dead don't dream.| And that crown is real gold."));
                    break;
                case "crown_off":
                    if (Bump("king_crown_off") == 0) Run(Narrate("The crown rings across the floor.^{t}Wake up{/}, and see what he is without it."));
                    break;
                case "bare":
                    if (Bump("king_bare") == 0) Run(Say("Kurashtar", "MY CROWN.", "king"));
                    else if (Count("king_bare") == 2) Run(Say("Kurashtar", "Stop DOING that.", "king"));
                    break;
                case "crowned":
                    if (king && king.Round >= 1 && Bump("king_guard" + king.Round) == 0) CallGuard(king.Round);
                    break;
            }
        }

        /// <summary>The second time he has to put his crown back on, he stops fighting alone.</summary>
        void CallGuard(int round)
        {
            var m = Map.Current;
            if (!m) return;
            var spots = round == 1 ? new[] { new Vector2(60, 200) } : new[] { new Vector2(60, 270), new Vector2(m.data.w - 60, 270) };
            foreach (var s in spots)
            {
                var u = Ushabti.Spawn(Map.ToWorld(s.x, s.y));
                u.Rouse();
            }
            // and in the dream, where his guard cannot follow, the gold draws moths
            if (Moth.All2() < 3)
                foreach (var s in new[] { new Vector2(120, 150), new Vector2(m.data.w - 120, 330) }) Moth.Spawn(Map.ToWorld(s.x, s.y));
            Run(Say("Kurashtar", round == 1 ? "GUARD." : "GUARDS.| Both of you.", "king"));
        }

        IEnumerator KingYields()
        {
            const string who = "Kurashtar";
            var p = Player.I;
            Set("king_done");
            Music.Stop();
            yield return Wait(0.6f);
            if (Dream.I.Dreaming) { Dream.I.Flip(p.pos, false); yield return Wait(0.8f); Dream.I.SetInstant(false); }
            // the watchman steps to the king's side, whichever he is nearer, and stands over him
            var way = new List<Vector2> { king.pos + new Vector2(p.pos.x >= king.pos.x ? 1.9f : -1.9f, -0.1f) };
            StartCoroutine(AzarWalks(way, king.pos));
            yield return CamTo(king.pos + new Vector2(0, -0.3f), 1.0f);
            while (azarWalking) yield return null;
            yield return Say(who, "Enough.| Enough.| I am so tired.", "king");
            yield return AzarSays("You've been awake four hundred years.");
            yield return Say(who, "Waiting to be woken.", "king");
            yield return AzarSays("You were never asleep. Nobody can wake a man who is standing by the door with his sandals on.");
            yield return Say(who, "...No.", "king");
            yield return Say(who, "I did not want to miss it. The morning. I thought: if I close my eyes they will blow it, and I shall not hear.", "king");
            Music.Play("summit");
            yield return AzarSays("Kurashtar.");
            yield return Say(who, "Nobody has said that in four hundred years.| Say it again.", "king");
            yield return AzarSays("Kurashtar. Give me the Horn. I'll blow it loud enough for both of us.");
            yield return Say(who, "Take it.", "king");
            yield return CamBack(0.6f);
            Set("item_horn");
            yield return ItemGet("dawn_horn", "You got the {g}DAWN HORN{/}!^It's a goat's horn.| Of course it is.");
            yield return Say(who, "If the god wakes, the sleep comes back up the hill. Then perhaps I shall try it.| Sleeping.| I am told it is very good.", "king");
            yield return Say(who, "Keep the noise down on your way out. People are trying to...| No. Nobody is. Make all the noise you like.", "king");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
            yield return Fade.Out(1.2f);
            yield return Card("Four hundred steps up.\nAgain.");
            Game.I.EnterMap("zig_3", null);
            Save.Write("zig_3", null);
            p.SetState(Player.State.Cutscene, "idle");
            yield return Dawn(true);
        }

        bool azarWalking;

        /// <summary>Azar walks to a spot because the story says so: straight there, stopping short if
        /// something stands in the way, and turning at the end to look at whatever he came to look at.</summary>
        IEnumerator AzarWalks(List<Vector2> way, Vector2 lookAt, float speed = 3.6f)
        {
            var p = Player.I;
            if (!p) yield break;
            azarWalking = true;
            var was = p.state;
            var half = new Vector2(0.28f, 0.14f);
            Facing Towards(Vector2 d) => Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x > 0 ? Facing.Right : Facing.Left) : (d.y > 0 ? Facing.Up : Facing.Down);
            bool walking = false, stopped = false;
            float t = 0;
            foreach (var to in way)
            {
                while (!stopped && t < 5f && Vector2.Distance(p.pos, to) > 0.05f)
                {
                    var d = to - p.pos;
                    var next = p.pos + Vector2.ClampMagnitude(d, speed * Time.deltaTime);
                    if (Solids.Overlaps(new Rect(next - half, half * 2), next, p)) { stopped = true; break; }
                    var f = Towards(d);
                    if (!walking || p.facing != f) { walking = true; p.Face(f); p.SetState(Player.State.Cutscene, "run"); }
                    p.pos = next;
                    t += Time.deltaTime;
                    yield return null;
                }
            }
            p.Face(Towards(lookAt - p.pos));
            p.SetState(was == Player.State.Talk ? Player.State.Talk : Player.State.Cutscene, "idle");
            azarWalking = false;
        }

        // ------------------------------------------------------------------ one breath of dawn
        public IEnumerator Dawn(bool arrived = false)
        {
            var p = Player.I;
            var m = Map.Current;
            Music.Stop();
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            p.SetState(Player.State.Cutscene, "idle");
            // the god and the priest are put there by the summit's own setup; give it a frame
            yield return null;
            while (!god) yield return null;
            // beside the sleeping god, facing him
            foreach (var off in new[] { new Vector2(-2.6f, -2.2f), new Vector2(2.6f, -2.2f), new Vector2(0, -3.2f) })
            {
                var at = god.pos + off;
                if (Solids.Overlaps(new Rect(at - p.half, p.half * 2), at, p)) continue;
                p.pos = at;
                break;
            }
            p.Face(Facing.Up);
            PixelView.I.SnapTo(p.pos);
            var goatEnd = Npc.Create("goat_dawn", p.pos + new Vector2(2.2f, -0.6f), "goat", "stare", WorldLayer.Both, Facing.Left, false);
            goatEnd.turnsToTalk = false;
            Fade.Set(1);
            yield return Fade.In(1.2f);
            yield return Wait(0.5f);
            yield return Narrate("The summit again. Ninhal, asleep. The High Priest, asleep.^The goat, already here.");
            yield return AzarSays("All right, old man.| Morning.");
            p.SetState(Player.State.ItemGet, "itemget");
            var held = new GameObject("Horn");
            var hs = held.AddComponent<SpriteRenderer>();
            hs.sharedMaterial = Map.SpriteMat;
            hs.sprite = Map.GetSprite("Items/dawn_horn", 8, 16);
            held.transform.position = (Vector3)(p.pos + new Vector2(0, 2.55f));
            hs.sortingOrder = Map.Order(p.pos.y) + 2;
            yield return Wait(0.6f);
            Sfx.Play("horn", 1f, 0f);
            yield return Wait(1.2f);
            yield return CamTo(god.pos + new Vector2(0, -1.0f), 1.4f);
            // the sky goes gold: one breath of it
            var v = PixelView.I;
            var night = v.ambient;
            var day = new Color(1.25f, 1.02f, 0.72f);
            Sfx.Play("dawn_swell", 1f, 0f);
            Music.Play("dawn");
            v.Shake(1, 2.5f);
            for (float t = 0; t < 1f; t += Time.deltaTime / 2.6f) { v.ambient = Color.Lerp(night, day, Mathf.SmoothStep(0, 1, t)); yield return null; }
            v.ambient = day;
            yield return Say("Ninhal", "...mmh.| Is it...| morning...", "god");
            yield return Narrate("For one breath, it is.^Gold comes over the edge of the world. Down in Ashkel, forty nights of dough rise all at once.");
            yield return Wait(0.5f);
            yield return Say("Ninhal", "...Ten more minutes.", "god");
            Sfx.Play("god_rumble");
            for (float t = 0; t < 1f; t += Time.deltaTime / 2.2f) { v.ambient = Color.Lerp(day, night, Mathf.SmoothStep(0, 1, t)); yield return null; }
            v.ambient = night;
            Destroy(held);
            p.SetState(Player.State.Cutscene, "idle");
            yield return CamBack(1.0f);
            yield return Wait(0.4f);
            yield return AzarSays("Ten.| That's five more than last time.");
            Sfx.Play("ghost_sigh", 0.9f, 0f);
            yield return Narrate("On the Hill of Sleepers, four hundred years of the dead lay down in that one breath of morning, and were asleep before it ended.^Nobody up there was going to hand it back.");
            // the goat has a look at the horn
            goatEnd.FaceTowards(p.pos);
            p.Face(goatEnd.pos.x > p.pos.x ? Facing.Right : Facing.Left);
            yield return Wait(0.6f);
            yield return Narrate("The goat looks at the Horn. Then at you.^It has both of its own. It checks anyway.");
            yield return AzarSays("It's not yours.| ...Is it?");
            goatEnd.Play("bleat", true);
            Sfx.Play("goat");
            yield return Wait(1.0f);
            goatEnd.SetIdle("stare");
            yield return AzarSays("I'm not asking.");
            ApplyItems();
            Set("chapter2_done");
            Save.Write(Game.I.CurrentMap, null);
            yield return Fade.Out(1.0f);
            yield return Card("END OF CHAPTER TWO",
                "The dead are asleep.\nThe living are thinking about it.",
                "Ninhal has asked for ten more minutes.\nAzar has a horn, and all night.",
                "WAKEFIRE\nmade by Randy Kundinger",
                "Thank you for staying awake.");
            if (goatEnd) Destroy(goatEnd.gameObject);
            Title.Show();
            yield return Fade.In(0.8f);
        }
    }
}
