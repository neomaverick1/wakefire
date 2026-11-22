// What each place is called when the game has to say where you are: on the banner as you walk in,
// on a save, and on the screen that asks where to wake.
namespace Wakefire
{
    public static class Places
    {
        public static string Name(string map) => map switch
        {
            "ashkel" => "The Temple Gate",
            "lowtown" => "The Lower Town",
            "terraces" => "The Olive Terraces",
            "cliffs" => "The Sea Cliffs",
            "temple_yard" => "The Temple Yard",
            "zig_1" => "The Ziggurat: First Hall",
            "zig_2" => "The Ziggurat: Hall of the Bull",
            "zig_3" => "The Summit",
            "necro_road" => "The Road of the Dead",
            "necropolis" => "The Hill of Sleepers",
            "tomb_1" => "The Tomb: Hall of Servants",
            "tomb_2" => "The Tomb: Hall of the Lyre",
            "tomb_3" => "The King's Chamber",
            _ => "Ashkel",
        };
    }
}
