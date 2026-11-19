using UnityEngine;

namespace BorrowedTime
{
    /// <summary>The crosshair: one ray from the camera finds what you look at within reach (props, walls, windows, stashes).
    /// E does its main verb, G or right-click the other. Holding something: E puts it down, G or click throws it.</summary>
    [RequireComponent(typeof(Player))]
    public class Interact : MonoBehaviour
    {
        public const float Reach = 2.8f;
        Player pl;
        Camera cam;
        CharacterController cc;
        public Rigidbody Held { get; private set; }
        int heldLayer;
        Thing lookThing;
        Panel lookPanel;
        Vector3 lookPoint;
        GUIStyle label;

        void Start() { pl = GetComponent<Player>(); cc = GetComponent<CharacterController>(); cam = Camera.main; }

        Vector3 Chest => transform.position + Vector3.up * 1.3f;

        void Update()
        {
            lookThing = null; lookPanel = null;
            if (Game.I == null || Game.I.Over || cam == null) { if (Held != null) Release(Vector3.zero); return; }
            if (Held == null && heldLayer != 0) heldLayer = 0;   // what we held was destroyed (restart, smash)
            Look();
            bool main = Input.GetKeyDown(KeyCode.E), alt = Input.GetKeyDown(KeyCode.G) || Input.GetMouseButtonDown(1);
            if (Held != null)
            {
                if (main) Release(pl.Velocity * 0.5f);
                else if (alt) Throw();
                return;
            }
            if (main || alt) Do(alt);
        }

        void Look()
        {
            Vector3 o = cam.transform.position, d = cam.transform.forward;
            float len = pl.FirstPerson ? Reach : Vector3.Distance(o, Chest) + Reach;
            if (!Physics.Raycast(o, d, out RaycastHit hit, len, ~(1 << 2), QueryTriggerInteraction.Collide)) return;
            if (!pl.FirstPerson && Vector3.Distance(hit.point, Chest) > Reach + 0.4f) return;   // third person: near you, not near the camera
            lookPoint = hit.point;
            lookThing = hit.collider.GetComponentInParent<Thing>();
            if (lookThing == null) lookPanel = hit.collider.GetComponent<Panel>();
            if (lookPanel != null && (lookPanel.dead || lookPanel.falling)) lookPanel = null;
        }

        public string Prompt()
        {
            if (Held != null) return "[E] Put down   [G / click] Throw";
            if (pl.Seated) return "[E] Get up";
            if (lookThing != null)
            {
                var (m, a) = Thing.Verbs(lookThing.kind);
                if (lookThing.kind == Kind.TrashCan && lookThing.used) m = "Pick up";
                return Thing.Name(lookThing.kind) + "   [E] " + m + (a != null ? "   [G] " + a : "");
            }
            if (lookPanel != null) return lookPanel.mtl == Mtl.Glass ? "Window   [E] Knock   [G] Punch" : (lookPanel.roof ? "Roof" : "Wall") + "   [E] Look closer   [G] Punch";
            return null;
        }

        public bool HasTarget => lookThing != null || lookPanel != null;

        void Do(bool alt)
        {
            var g = Game.I;
            if (pl.Seated) { if (!alt) pl.StandUp(); return; }
            if (lookPanel != null)
            {
                Vector3 dir = cam.transform.forward;
                if (lookPanel.mtl == Mtl.Glass && !alt) { g.Toast("KNOCK KNOCK"); return; }
                if (!alt) { g.Toast(Mathf.RoundToInt(100f * lookPanel.hp / lookPanel.hp0) + "% left in it"); return; }
                if (!lookPanel.Hit(32f, lookPoint, dir)) g.Toast(lookPanel.mtl == Mtl.Glass ? "CRACK" : "OW");
                return;
            }
            if (lookThing == null) return;
            var t = lookThing;
            var rb = t.GetComponent<Rigidbody>();
            switch (t.kind)
            {
                case Kind.Crate:
                    if (!alt) Grab(rb); else { g.SmashCrate(t); }
                    break;
                case Kind.TrashCan:
                    if (alt || t.used) { Grab(rb); break; }
                    t.used = true;
                    float r = Random.value;
                    if (r < 0.4f) g.AddDollas(Random.Range(1, 7), "loose change");
                    else if (r < 0.7f) g.AddLife(3f, "half a sandwich +3s");
                    else g.Toast("nothing but bad smells");
                    break;
                case Kind.Couch:
                    if (!alt) { pl.SitOn(t); break; }
                    if (t.used) { g.Toast("already searched"); break; }
                    t.used = true;
                    if (Random.value < 0.6f) g.AddDollas(Random.Range(2, 9), "cushion money"); else g.Toast("crumbs");
                    break;
                case Kind.Table:
                    if (!alt) Grab(rb);
                    else if (rb != null)
                    {
                        rb.AddForce(Vector3.up * rb.mass * 6f, ForceMode.Impulse);
                        rb.AddTorque(Vector3.Cross(Vector3.up, cam.transform.forward).normalized * rb.mass * 4f, ForceMode.Impulse);
                        g.AddChaos(20, "TABLE FLIP");
                    }
                    break;
                case Kind.Fridge:
                    if (alt) { if (rb != null) rb.AddForceAtPosition(Flat(cam.transform.forward) * 420f, lookPoint, ForceMode.Impulse); g.Toast("SHOVE"); break; }
                    if (t.used) { g.Toast("the fridge is empty"); break; }
                    t.used = true; g.AddLife(2f, "a cold snack +2s");
                    break;
                case Kind.Car:
                    if (!alt) { g.AddChaos(5, "HOOONK"); break; }
                    if (t.used) { g.Toast("locked"); break; }
                    t.used = true;
                    float c = Random.value;
                    if (c < 0.4f) g.Toast("locked");
                    else if (c < 0.7f) g.AddChaos(40, "CAR ALARM");
                    else g.AddDollas(3, "change in the cup holder");
                    break;
                case Kind.Stash:
                    g.TakeStash(t.transform);
                    break;
                default:
                    if (!alt) Grab(rb); else if (rb != null) rb.AddForce((Flat(cam.transform.forward) + Vector3.up * 0.4f) * 6f, ForceMode.VelocityChange);
                    break;
            }
        }

        static Vector3 Flat(Vector3 v) { v.y = 0f; return v.normalized; }

        void Grab(Rigidbody rb)
        {
            if (!Thing.Liftable(rb)) { Game.I.Toast("too heavy"); return; }
            Held = rb;
            heldLayer = rb.gameObject.layer;
            rb.gameObject.layer = 2;   // out of the crosshair and the camera's wall check
            foreach (var col in rb.GetComponentsInChildren<Collider>()) Physics.IgnoreCollision(cc, col, true);
            rb.useGravity = false;
        }

        void Release(Vector3 v)
        {
            var rb = Held; Held = null;
            if (rb == null) return;
            rb.gameObject.layer = heldLayer;
            foreach (var col in rb.GetComponentsInChildren<Collider>()) Physics.IgnoreCollision(cc, col, false);
            rb.useGravity = true;
            rb.linearVelocity = v;
        }

        /// <summary>Throws what you hold where you look, with a small arc.</summary>
        public void Throw()
        {
            if (Held == null) return;
            float speed = Mathf.Lerp(16f, 8f, Mathf.InverseLerp(5f, 40f, Held.mass));
            Vector3 dir = (cam.transform.forward + Vector3.up * 0.12f).normalized;
            var rb = Held;
            Release(dir * speed + pl.Velocity);
            rb.AddTorque(Random.insideUnitSphere * 3f, ForceMode.VelocityChange);
            Game.I.AddChaos(5, "YEET");
        }

        void FixedUpdate()
        {
            if (Held == null) return;
            Vector3 target = pl.FirstPerson
                ? cam.transform.position + cam.transform.forward * 1.0f + Vector3.down * 0.35f
                : Chest + transform.forward * 0.85f;
            Vector3 to = target - Held.position;
            if (to.magnitude > 3f) { Release(Vector3.zero); return; }   // snagged on something
            Held.linearVelocity = Vector3.ClampMagnitude(to / Time.fixedDeltaTime * 0.5f, 20f);
            Held.angularVelocity *= 0.6f;
        }

        void OnGUI()
        {
            if (Game.I == null || Game.I.Over) return;
            if (label == null) label = new GUIStyle(GUI.skin.label) { fontSize = 18, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
            float k = Screen.height / 720f;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(k, k, 1f));
            float w = Screen.width / k, cx = w / 2f, cy = 360f;
            if (pl.FirstPerson)
            {
                GUI.color = HasTarget ? new Color(1f, 0.82f, 0.3f) : new Color(1f, 1f, 1f, 0.8f);
                float s = HasTarget ? 14f : 6f;
                GUI.DrawTexture(new Rect(cx - s / 2f, cy - s / 2f, s, s), Texture2D.whiteTexture);
                GUI.color = Color.white;
            }
            string p = Prompt();
            if (p != null)
            {
                GUI.Box(new Rect(cx - 260f, cy + 40f, 520f, 34f), GUIContent.none);
                GUI.Label(new Rect(cx - 260f, cy + 40f, 520f, 34f), p, label);
            }
        }
    }
}
