using UnityEngine;

namespace BorrowedTime
{
    public enum Kind { Crate, TrashCan, Couch, Table, Fridge, Car, Stash, Plank }

    /// <summary>Something you can look at and use: a name and two verbs (E does the main one, G or right-click the other).</summary>
    public class Thing : MonoBehaviour
    {
        public Kind kind;
        public bool used;   // one-time loot (rummaged, searched, opened) is spent

        public static string Name(Kind k) => k switch
        {
            Kind.Crate => "Crate", Kind.TrashCan => "Trash can", Kind.Couch => "Couch", Kind.Table => "Table",
            Kind.Fridge => "Fridge", Kind.Car => "Car", Kind.Stash => "Stash", _ => "Plank",
        };

        /// <summary>The main and the other verb; null where there is none.</summary>
        public static (string main, string alt) Verbs(Kind k) => k switch
        {
            Kind.Crate => ("Pick up", "Smash it"),
            Kind.TrashCan => ("Rummage", "Pick up"),
            Kind.Couch => ("Sit", "Search the cushions"),
            Kind.Table => ("Pick up", "Flip it over"),
            Kind.Fridge => ("Open it", "Shove"),
            Kind.Car => ("Honk the horn", "Try the door"),
            Kind.Stash => ("Take it", null),
            _ => ("Pick up", "Kick"),
        };

        public static bool Liftable(Rigidbody rb) => rb != null && !rb.isKinematic && rb.mass <= 40f;
    }
}
