using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace BorrowedTime
{
    public enum Mtl { Wood, Roof, Brick, Glass }

    /// <summary>Material data. Wood and roof use effective densities for framed construction (about 40–50 kg per m²).</summary>
    public static class MtlData
    {
        public static float Hp(Mtl m) => m == Mtl.Wood ? 110f : m == Mtl.Roof ? 150f : m == Mtl.Brick ? 280f : 28f;
        public static float Density(Mtl m) => m == Mtl.Wood ? 250f : m == Mtl.Roof ? 70f : m == Mtl.Brick ? 1900f : 2500f;
        public static float Cell(Mtl m) => m == Mtl.Wood ? 0.8f : m == Mtl.Roof ? 1.2f : m == Mtl.Brick ? 0.6f : 0.45f;
        public static int Points(Mtl m) => m == Mtl.Wood ? 110 : m == Mtl.Roof ? 160 : m == Mtl.Brick ? 220 : 70;
    }

    /// <summary>One breakable piece of a building: a wall panel, a window or a roof half.
    /// Damage is kinetic energy (½·m·v², divided by 100) of whatever hits it.</summary>
    public class Panel : MonoBehaviour
    {
        public Building building;
        public Mtl mtl;
        public bool roof, ground, falling, dead, stable = true;
        public float hp, hp0;
        public Bounds box;   // axis-aligned footprint used by the support graph
        public readonly List<Panel> sup = new List<Panel>(), lat = new List<Panel>(), ups = new List<Panel>();

        public bool Hit(float dmg, Vector3 point, Vector3 dir)
        {
            if (dead || falling || dmg <= 0f) return false;
            hp -= dmg;
            if (hp > 0f) return false;
            dead = true;
            if (Game.I != null) Game.I.OnPanelBroken(this, point);
            Rubble.Fracture(this, point, dir, dmg, null);
            Destroy(gameObject);
            building.Recheck();
            return true;
        }

        /// <summary>Lost its load path: becomes a rigid body that falls and shatters when it lands hard.</summary>
        public void Detach()
        {
            if (dead) return;
            falling = true;
            var s = transform.lossyScale;
            var rb = gameObject.AddComponent<Rigidbody>();
            rb.mass = Mathf.Max(5f, s.x * s.y * s.z * MtlData.Density(mtl));
            rb.interpolation = RigidbodyInterpolation.Interpolate;
            rb.AddTorque(Random.insideUnitSphere * rb.mass * 0.5f, ForceMode.Impulse);
            gameObject.AddComponent<Slab>().panel = this;
        }

        void OnCollisionEnter(Collision c)
        {
            // flying props and thrown cars break walls: ½·m·v² from the contact impulse
            if (c.rigidbody == null || falling) return;
            float m = c.rigidbody.mass, v = c.impulse.magnitude / Mathf.Max(1f, m);
            if (v > 4f) Hit(0.5f * Mathf.Min(m, 400f) * v * v / 100f, c.GetContact(0).point, -c.GetContact(0).normal);
        }
    }

    /// <summary>A detached panel. Breaks up when it decelerates by more than 3.5 m/s in one contact, and damages what it lands on.</summary>
    public class Slab : MonoBehaviour
    {
        public Panel panel;
        float born;

        void Start() { born = Time.time; }

        void OnCollisionEnter(Collision c)
        {
            if (panel == null || panel.dead) return;
            var rb = GetComponent<Rigidbody>();
            var other = c.collider.GetComponent<Panel>();
            var point = c.contactCount > 0 ? c.GetContact(0).point : transform.position;
            if (other != null && !other.dead) other.Hit(c.impulse.magnitude / 40f, point, Vector3.down);
            if (c.impulse.magnitude / rb.mass > 3.5f || Time.time - born > 8f)
            {
                panel.dead = true;
                if (Game.I != null) Game.I.OnPanelBroken(panel, point);
                Rubble.Fracture(panel, point, Vector3.up, panel.hp0 * 0.8f, rb);
                Destroy(gameObject);
            }
        }
    }

    /// <summary>Owns a building's panels and decides what stays up after each break.</summary>
    public class Building : MonoBehaviour
    {
        public readonly List<Panel> panels = new List<Panel>();

        static float Ov(float a0, float a1, float b0, float b1) => Mathf.Min(a1, b1) - Mathf.Max(a0, b0);

        /// <summary>Support graph: who rests on whom (vertical) and who is bonded side by side in the same course (lateral).</summary>
        public void Finish()
        {
            foreach (var b in panels) b.ground = !b.roof && b.box.min.y < 0.06f;
            foreach (var b in panels)
                foreach (var a in panels)
                {
                    if (a == b || a.roof) continue;
                    float ox = Ov(b.box.min.x, b.box.max.x, a.box.min.x, a.box.max.x), oz = Ov(b.box.min.z, b.box.max.z, a.box.min.z, a.box.max.z);
                    if (Mathf.Abs(a.box.max.y - b.box.min.y) < 0.06f && ox > 0.02f && oz > 0.02f) { b.sup.Add(a); a.ups.Add(b); }
                    else if (!b.roof && Ov(b.box.min.y, b.box.max.y, a.box.min.y, a.box.max.y) > 0.1f
                             && ((Mathf.Abs(ox) < 0.03f && oz > 0.02f) || (Mathf.Abs(oz) < 0.03f && ox > 0.02f))) b.lat.Add(a);
                }
        }

        /// <summary>0-1 breadth-first search from grounded panels: going up costs nothing, each sideways step costs one, at most two in a row.
        /// A roof stays only while at least half of the panels under it stand.</summary>
        public void Recheck()
        {
            var best = new Dictionary<Panel, int>();
            var dq = new LinkedList<Panel>();
            foreach (var p in panels) { p.stable = false; if (!p.dead && !p.falling && p.ground) { best[p] = 0; dq.AddLast(p); } }
            while (dq.Count > 0)
            {
                var p = dq.First.Value; dq.RemoveFirst();
                int h = best[p]; p.stable = true;
                foreach (var u in p.ups)
                {
                    if (u.dead || u.falling || u.roof) continue;
                    if (!best.TryGetValue(u, out int bu) || bu > h) { best[u] = h; dq.AddFirst(u); }
                }
                if (h < 2)
                    foreach (var u in p.lat)
                    {
                        if (u.dead || u.falling) continue;
                        if (!best.TryGetValue(u, out int bu) || bu > h + 1) { best[u] = h + 1; dq.AddLast(u); }
                    }
            }
            foreach (var p in panels)
            {
                if (p.dead || p.falling || !p.roof) continue;
                int n = 0, k = 0;
                foreach (var s in p.sup) { n++; if (!s.dead && !s.falling && s.stable) k++; }
                p.stable = n > 0 && k * 2 >= n;
            }
            var bad = new List<Panel>();
            foreach (var p in panels) if (!p.dead && !p.falling && !p.stable) { p.falling = true; bad.Add(p); }
            if (bad.Count > 0) StartCoroutine(Collapse(bad));
        }

        IEnumerator Collapse(List<Panel> bad)
        {
            foreach (var p in bad)
            {
                if (p != null && !p.dead) { p.falling = false; p.Detach(); }
                yield return new WaitForSeconds(Random.Range(0.02f, 0.08f));
            }
        }
    }

    /// <summary>Pre-fracture into a jittered grid of boxes across the panel's two long axes (glass gets smaller shards).</summary>
    public static class Rubble
    {
        static readonly Queue<GameObject> chunks = new Queue<GameObject>();
        const int Cap = 260;

        static float[] Cuts(int n)
        {
            var c = new float[n + 1]; c[0] = 0f; c[n] = 1f;
            for (int i = 1; i < n; i++) c[i] = (i + Random.Range(-0.28f, 0.28f)) / n;
            return c;
        }

        public static void Fracture(Panel p, Vector3 point, Vector3 dir, float dmg, Rigidbody inherit)
        {
            var t = p.transform;
            Vector3 s = t.lossyScale;
            var mat = p.GetComponent<Renderer>().sharedMaterial;
            int thin = (s.x <= s.y && s.x <= s.z) ? 0 : (s.y <= s.z ? 1 : 2);
            int a0 = thin == 0 ? 1 : 0, a1 = thin == 2 ? 1 : 2;
            float cell = MtlData.Cell(p.mtl);
            int nu = Mathf.Clamp(Mathf.RoundToInt(s[a0] / cell), 1, 4), nv = Mathf.Clamp(Mathf.RoundToInt(s[a1] / cell), 1, 4);
            float[] cu = Cuts(nu), cv = Cuts(nv);
            float k = Mathf.Clamp(dmg / p.hp0, 0.6f, 4.5f);
            Vector3 d0 = dir.sqrMagnitude > 1e-6f ? dir.normalized : Vector3.up;
            Transform parent = Game.I != null ? Game.I.World : null;
            for (int i = 0; i < nu; i++)
                for (int j = 0; j < nv; j++)
                {
                    Vector3 lmin = new Vector3(-0.5f, -0.5f, -0.5f), lmax = new Vector3(0.5f, 0.5f, 0.5f);
                    lmin[a0] = cu[i] - 0.5f; lmax[a0] = cu[i + 1] - 0.5f; lmin[a1] = cv[j] - 0.5f; lmax[a1] = cv[j + 1] - 0.5f;
                    Vector3 wc = t.TransformPoint((lmin + lmax) * 0.5f);
                    Vector3 size = Vector3.Max(Vector3.Scale(lmax - lmin, s) - Vector3.one * 0.008f, Vector3.one * 0.03f);
                    var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    go.name = "Rubble";
                    if (parent != null) go.transform.SetParent(parent, true);
                    go.transform.SetPositionAndRotation(wc, t.rotation);
                    go.transform.localScale = size;
                    go.GetComponent<Renderer>().sharedMaterial = mat;
                    var rb = go.AddComponent<Rigidbody>();
                    rb.mass = Mathf.Max(0.5f, size.x * size.y * size.z * MtlData.Density(p.mtl));
                    Vector3 r = wc - point;
                    float push = 2.4f * k / (0.95f + r.magnitude);
                    Vector3 v = (inherit != null ? inherit.GetPointVelocity(wc) * 0.6f : Vector3.zero)
                              + d0 * push * 1.6f + (r.sqrMagnitude > 1e-6f ? r.normalized : Vector3.up) * push * 0.7f
                              + new Vector3(Random.Range(-0.8f, 0.8f), Random.Range(0.4f, 1.6f), Random.Range(-0.8f, 0.8f));
                    rb.linearVelocity = v;
                    rb.angularVelocity = Random.insideUnitSphere * (3f + push);
                    if (p.mtl == Mtl.Glass) Object.Destroy(go, Random.Range(6f, 9f));
                    chunks.Enqueue(go);
                    while (chunks.Count > Cap) { var old = chunks.Dequeue(); if (old != null) Object.Destroy(old); }
                }
        }
    }
}
