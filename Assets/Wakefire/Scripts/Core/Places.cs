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
            "crypt" => "The Crypt of the First Watch",
            "zig_1" => "The Ziggurat: Lower Halls",
            "zig_2" => "The Ziggurat: Halls of the Bull",
            "zig_hi" => "The Ziggurat: High Halls",
            "zig_3" => "The Summit",
            "barrow" => "The Generals' Barrow",
            "necro_road" => "The Road of the Dead",
            "necropolis" => "The Hill of Sleepers",
            "tomb_1" => "The King's Tomb: Outer Halls",
            "tomb_2" => "The King's Tomb: Inner Halls",
            "tomb_hi" => "The King's Tomb: The King's Road",
            "tomb_3" => "The King's Chamber",
            _ => "Ashkel",
        };

        /// <summary>The same places as the world map letters them.</summary>
        public static string Short(string map) => map switch
        {
            "ashkel" => "Temple Gate",
            "lowtown" => "Lower Town",
            "terraces" => "Olive Terraces",
            "cliffs" => "Sea Cliffs",
            "temple_yard" => "Temple Yard",
            "necro_road" => "Dead Road",
            "necropolis" => "Hill of Sleepers",
            _ => Name(map),
        };
    }
}
