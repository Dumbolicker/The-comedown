using System.Collections.Generic;
using UnityEngine;

namespace BorrowedTime
{
    /// <summary>Boots from an empty scene: builds the light, the street, walk-in houses, props, stashes and the player,
    /// then runs the draining clock and the HUD. Press R to rebuild everything.</summary>
    public class Game : MonoBehaviour
    {
        public static Game I;
        public Transform World { get; private set; }
        public bool Over { get; private set; }

        float life = 45f, stashT, toastT;
        int score, dollas, broken;
        string toast = "";
        Player player;
        readonly List<Vector3> spots = new List<Vector3>();
        readonly List<Transform> stashes = new List<Transform>();
        GUIStyle big, small, center;

        static readonly int[] WallCols = { 0xe8d5b0, 0xb8d4e3, 0xf2c6c2, 0xc9e4c5, 0xf5e6a8, 0xd9c2e8, 0xf0f0ea };
        static readonly int[] RoofCols = { 0x7a3b2e, 0x4a4a52, 0x3b5470, 0x5c4632 };
        static readonly int[] CarCols = { 0xb83a3a, 0x2c5fa8, 0xe8e4d8, 0x2b2b2b, 0x3c7a4a, 0xc8a03a };
        static readonly int[] SofaCols = { 0xa8843a, 0x7a4a3a, 0x5e7a4a, 0x8a5a7a };
        static Color Pick(int[] a) => Mat.Hex(a[Random.Range(0, a.Length)]);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (I == null) new GameObject("Borrowed Time").AddComponent<Game>();
        }

        void Awake() { I = this; Application.targetFrameRate = 60; }

        void Start()
        {
            BuildLightAndCamera();
            BuildWorld();
            var go = new GameObject("Player") { layer = 2 };
            go.AddComponent<CharacterController>();
            player = go.AddComponent<Player>();
            go.AddComponent<Interact>();
            go.transform.position = new Vector3(0f, 0.2f, 4.5f);
        }

        void BuildLightAndCamera()
        {
            var cam = new GameObject("Main Camera") { tag = "MainCamera" }.AddComponent<Camera>();
            cam.gameObject.AddComponent<AudioListener>();
            cam.fieldOfView = 60f; cam.nearClipPlane = 0.1f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional; sun.intensity = 1.25f; sun.color = new Color(1f, 0.95f, 0.86f); sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
            RenderSettings.sun = sun;
            var sky = Resources.Load<Material>("BT_Sky"); if (sky != null) RenderSettings.skybox = sky;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.7f, 0.85f); RenderSettings.ambientEquatorColor = new Color(0.55f, 0.55f, 0.52f); RenderSettings.ambientGroundColor = new Color(0.32f, 0.3f, 0.26f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 60f; RenderSettings.fogEndDistance = 230f; RenderSettings.fogColor = new Color(0.72f, 0.8f, 0.9f);
            QualitySettings.shadows = ShadowQuality.All; QualitySettings.shadowResolution = ShadowResolution.High; QualitySettings.shadowDistance = 80f; QualitySettings.antiAliasing = 4;
        }

        GameObject Box(string name, Vector3 c, Vector3 size, Material m, bool collider = true, Transform parent = null)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent != null ? parent : World, false);
            go.transform.position = c; go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = m;
            if (!collider) Destroy(go.GetComponent<Collider>());
            return go;
        }

        GameObject Prop(string name, Vector3 c, Vector3 size, Material m, float mass, Transform parent = null, Kind kind = Kind.Plank)
        {
            var go = Box(name, c, size, m, true, parent);
            var rb = go.AddComponent<Rigidbody>(); rb.mass = mass; rb.interpolation = RigidbodyInterpolation.Interpolate;
            go.AddComponent<Thing>().kind = kind;
            return go;
        }

        void BuildWorld()
        {
            World = new GameObject("World").transform;
            Box("Ground", new Vector3(0f, -0.5f, 0f), new Vector3(400f, 1f, 400f), Mat.Get(Mat.Hex(0x5f7d45), 0.05f));
            Box("Road", new Vector3(0f, 0.005f, 0f), new Vector3(170f, 0.01f, 9f), Mat.Get(Mat.Hex(0x2f2e36), 0.15f), false);
            foreach (float z in new[] { -5.75f, 5.75f }) Box("Sidewalk", new Vector3(0f, 0.075f, z), new Vector3(170f, 0.15f, 2.5f), Mat.Get(Mat.Hex(0xa9a59c), 0.1f));
            for (float x = -82f; x < 82f; x += 4f) Box("Lane", new Vector3(x, 0.02f, 0f), new Vector3(2f, 0.02f, 0.16f), Mat.Get(Mat.Hex(0xe8c84a), 0.2f), false);
            for (int i = 0; i < 4; i++) { House(-36f + i * 22f, 14.5f, true); House(-36f + i * 22f, -14.5f, false); }
            for (int i = 0; i < 6; i++)
            {
                float x = -60f + i * 24f;
                Box("Lamp post", new Vector3(x, 3f, 7.2f), new Vector3(0.18f, 6f, 0.18f), Mat.Get(Mat.Hex(0x3a3d42), 0.4f, 0.6f));
                Prop("Crate", new Vector3(x + 6f, 0.6f, 6.6f), new Vector3(0.9f, 0.9f, 0.9f), Mat.Get(Mat.Hex(0xa67c4a), 0.15f), 30f, null, Kind.Crate);
                Prop("Trash can", new Vector3(x + 3f, 0.6f, -6.5f), new Vector3(0.62f, 1f, 0.62f), Mat.Get(Mat.Hex(0x6e757c), 0.5f, 0.4f), 12f, null, Kind.TrashCan);
            }
            Car(new Vector3(-12f, 0f, 2.6f), 90f); Car(new Vector3(18f, 0f, -2.6f), -90f);
            for (int i = 0; i < 4; i++) SpawnStash();
        }

        void Car(Vector3 at, float yaw)
        {
            var car = new GameObject("Car").transform;
            car.SetParent(World, false); car.SetPositionAndRotation(at + Vector3.up * 0.8f, Quaternion.Euler(0f, yaw, 0f));
            var body = Box("Body", car.position, new Vector3(1.9f, 0.7f, 4.2f), Mat.Get(Pick(CarCols), 0.75f, 0.3f), false, car);
            body.transform.localPosition = new Vector3(0f, -0.05f, 0f); body.transform.localRotation = Quaternion.identity;
            var cabin = Box("Cabin", car.position, new Vector3(1.7f, 0.55f, 2.1f), Mat.Get(Mat.Hex(0x22303c), 0.9f), false, car);
            cabin.transform.localPosition = new Vector3(0f, 0.55f, -0.2f); cabin.transform.localRotation = Quaternion.identity;
            foreach (var w in new[] { new Vector3(0.85f, -0.42f, 1.35f), new Vector3(-0.85f, -0.42f, 1.35f), new Vector3(0.85f, -0.42f, -1.35f), new Vector3(-0.85f, -0.42f, -1.35f) })
            {
                var wheel = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                Destroy(wheel.GetComponent<Collider>());
                wheel.transform.SetParent(car, false);
                wheel.transform.localPosition = w; wheel.transform.localRotation = Quaternion.Euler(0f, 0f, 90f); wheel.transform.localScale = new Vector3(0.66f, 0.12f, 0.66f);
                wheel.GetComponent<Renderer>().sharedMaterial = Mat.Get(Mat.Hex(0x161618), 0.2f);
            }
            var col = car.gameObject.AddComponent<BoxCollider>(); col.center = new Vector3(0f, -0.25f, 0f); col.size = new Vector3(1.9f, 1.0f, 4.2f);
            var rb = car.gameObject.AddComponent<Rigidbody>(); rb.mass = 1200f; rb.interpolation = RigidbodyInterpolation.Interpolate;
            car.gameObject.AddComponent<Thing>().kind = Kind.Car;
        }

        struct Opening
        {
            public float u0, u1, y0, y1; public bool door;
            public Opening(float a, float b, float c, float d, bool isDoor = false) { u0 = a; u1 = b; y0 = c; y1 = d; door = isDoor; }
        }

        /// <summary>Walk-in house: wood-frame walls of breakable panels (doorway, glass windows), a two-part breakable roof, furniture, a ceiling light.</summary>
        void House(float cx, float cz, bool frontNeg)
        {
            var root = new GameObject("House").transform; root.SetParent(World, false);
            var b = root.gameObject.AddComponent<Building>();
            float hw = Random.Range(2.8f, 3.5f), hd = Random.Range(2.5f, 3.0f), wh = Random.Range(2.9f, 3.3f), rh = Random.Range(1.4f, 2.0f), t = 0.18f;
            float x0 = cx - hw, x1 = cx + hw, z0 = cz - hd, z1 = cz + hd, fz0 = frontNeg ? z0 : z1 - t, bz0 = frontNeg ? z1 - t : z0;
            Material wall = Mat.Get(Pick(WallCols), 0.25f), roof = Mat.Get(Pick(RoofCols), 0.15f);
            Opening Win(float u, float w) => new Opening(u - w / 2f, u + w / 2f, 0.95f, 1.95f);
            WallRun(b, true, x0, x1, fz0, fz0 + t, 0f, wh, new[] { new Opening(cx - 0.6f, cx + 0.6f, 0f, 2.1f, true), Win(cx - hw * 0.6f, 1f), Win(cx + hw * 0.6f, 1f) }, Mtl.Wood, wall);
            WallRun(b, true, x0, x1, bz0, bz0 + t, 0f, wh, new[] { Win(cx - hw * 0.45f, 1.1f), Win(cx + hw * 0.45f, 1.1f) }, Mtl.Wood, wall);
            WallRun(b, false, z0 + t, z1 - t, x0, x0 + t, 0f, wh, new[] { Win(cz, 1f) }, Mtl.Wood, wall);
            WallRun(b, false, z0 + t, z1 - t, x1 - t, x1, 0f, wh, new[] { Win(cz, 1f) }, Mtl.Wood, wall);
            RoofHalf(b, x0 - 0.3f, x1 + 0.3f, z0 - 0.3f, cz, wh, rh, true, roof);
            RoofHalf(b, x0 - 0.3f, x1 + 0.3f, cz, z1 + 0.3f, wh, rh, false, roof);
            b.Finish();
            Box("Floor", new Vector3(cx, 0.02f, cz), new Vector3(hw * 2f - 0.4f, 0.02f, hd * 2f - 0.4f), Mat.Get(Mat.Hex(0x9a6b42), 0.35f), false, root);
            float fd = frontNeg ? -1f : 1f, back = cz - fd * (hd - 0.65f);
            Prop("Couch", new Vector3(cx - 0.9f, 0.46f, back), new Vector3(2f, 0.9f, 0.9f), Mat.Get(Pick(SofaCols), 0.1f), 90f, root, Kind.Couch);
            Prop("Table", new Vector3(cx + hw * 0.45f, 0.41f, cz), new Vector3(1.2f, 0.8f, 0.8f), Mat.Get(Mat.Hex(0x8a6038), 0.3f), 25f, root, Kind.Table);
            Prop("Fridge", new Vector3(x1 - 0.6f, 0.91f, back), new Vector3(0.7f, 1.8f, 0.7f), Mat.Get(Mat.Hex(0xeef0f2), 0.6f), 70f, root, Kind.Fridge);
            var lamp = new GameObject("Ceiling light").AddComponent<Light>();
            lamp.transform.SetParent(root, false); lamp.transform.position = new Vector3(cx, wh - 0.4f, cz);
            lamp.type = LightType.Point; lamp.range = 7f; lamp.intensity = 1.1f; lamp.color = new Color(1f, 0.85f, 0.65f);
            spots.Add(new Vector3(cx + hw * 0.35f, 0f, cz)); spots.Add(new Vector3(cx, 0f, frontNeg ? z0 - 3f : z1 + 3f));
        }

        void WallRun(Building b, bool alongX, float a0, float a1, float t0, float t1, float y0, float y1, Opening[] ops, Mtl m, Material mat, float course = 2.1f)
        {
            var cuts = new List<float> { a0, a1 };
            foreach (var o in ops) { cuts.Add(Mathf.Clamp(o.u0, a0, a1)); cuts.Add(Mathf.Clamp(o.u1, a0, a1)); }
            cuts.Sort();
            var cols = new List<Vector2>();
            for (int i = 0; i < cuts.Count - 1; i++)
            {
                float len = cuts[i + 1] - cuts[i]; if (len < 0.03f) continue;
                int n = Mathf.Max(1, Mathf.CeilToInt(len / 1.5f));
                for (int k = 0; k < n; k++) cols.Add(new Vector2(cuts[i] + len * k / n, cuts[i] + len * (k + 1) / n));
            }
            float tm = (t0 + t1) * 0.5f, mid = Mathf.Min(course, y1);
            void P(float u0, float u1, float ya, float yb, Mtl mm, Material ma, float ta, float tb)
            {
                if (yb - ya < 0.04f) return;
                Vector3 mn = alongX ? new Vector3(u0, ya, ta) : new Vector3(ta, ya, u0), mx = alongX ? new Vector3(u1, yb, tb) : new Vector3(tb, yb, u1);
                MakePanel(b, mn, mx, mm, ma);
            }
            foreach (var c in cols)
            {
                float um = (c.x + c.y) * 0.5f; Opening? op = null;
                foreach (var o in ops) if (um > o.u0 && um < o.u1) { op = o; break; }
                if (op.HasValue && op.Value.door) { var o = op.Value; P(c.x, c.y, Mathf.Max(o.y1, y0), Mathf.Max(o.y1, mid), m, mat, t0, t1); P(c.x, c.y, Mathf.Max(o.y1, mid), y1, m, mat, t0, t1); }
                else if (op.HasValue)
                {
                    var o = op.Value;
                    P(c.x, c.y, y0, o.y0, m, mat, t0, t1); P(c.x, c.y, o.y0, o.y1, Mtl.Glass, Mat.Glass(), tm - 0.025f, tm + 0.025f);
                    P(c.x, c.y, o.y1, Mathf.Max(o.y1, mid), m, mat, t0, t1); P(c.x, c.y, Mathf.Max(o.y1, mid), y1, m, mat, t0, t1);
                }
                else { P(c.x, c.y, y0, mid, m, mat, t0, t1); P(c.x, c.y, mid, y1, m, mat, t0, t1); }
            }
        }

        Panel MakePanel(Building b, Vector3 mn, Vector3 mx, Mtl m, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = m.ToString(); go.transform.SetParent(b.transform, false);
            Vector3 c = (mn + mx) * 0.5f, s = mx - mn;
            go.transform.position = c; go.transform.localScale = s;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            var p = go.AddComponent<Panel>();
            p.building = b; p.mtl = m; p.hp = p.hp0 = MtlData.Hp(m); p.box = new Bounds(c, s);
            b.panels.Add(p);
            return p;
        }

        void RoofHalf(Building b, float x0, float x1, float za, float zb, float wh, float rh, bool risesTowardB, Material mat)
        {
            float xc = (x0 + x1) * 0.5f;
            Vector3 eave = new Vector3(xc, wh, risesTowardB ? za : zb), ridge = new Vector3(xc, wh + rh, risesTowardB ? zb : za), dir = ridge - eave;
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "Roof"; go.transform.SetParent(b.transform, false);
            go.transform.SetPositionAndRotation((eave + ridge) * 0.5f + Vector3.up * 0.1f, Quaternion.LookRotation(dir.normalized, Vector3.up));
            go.transform.localScale = new Vector3(x1 - x0, 0.2f, dir.magnitude);
            go.GetComponent<Renderer>().sharedMaterial = mat;
            var p = go.AddComponent<Panel>();
            p.building = b; p.mtl = Mtl.Roof; p.roof = true; p.hp = p.hp0 = MtlData.Hp(Mtl.Roof);
            p.box = new Bounds(new Vector3(xc, wh + rh * 0.5f, (za + zb) * 0.5f), new Vector3(x1 - x0, rh, zb - za));
            b.panels.Add(p);
        }

        void SpawnStash()
        {
            if (spots.Count == 0) return;
            Vector3 p = spots[Random.Range(0, spots.Count)];
            Color col = Color.HSVToRGB(Random.value, 0.7f, 1f);
            var go = Box("Stash", p + Vector3.up * 0.9f, Vector3.one * 0.35f, Mat.Get(col, 0.6f, 0f, col * 2.2f));
            go.GetComponent<Collider>().isTrigger = true;   // you walk through it; the crosshair still finds it
            go.AddComponent<Thing>().kind = Kind.Stash;
            var l = go.AddComponent<Light>(); l.type = LightType.Point; l.color = col; l.range = 4f; l.intensity = 1.5f;
            stashes.Add(go.transform);
        }

        public void Toast(string msg) { toast = msg; toastT = 1.5f; }
        public void AddLife(float s, string msg) { life = Mathf.Min(240f, life + s); Toast(msg); }
        public void AddDollas(int d, string msg) { dollas += d; Toast(msg + " +Ð " + d); }
        public void AddChaos(int pts, string msg) { score += pts; Toast(msg + " +" + pts); }

        public void TakeStash(Transform s)
        {
            int i = stashes.IndexOf(s);
            if (i < 0) return;
            life = Mathf.Min(240f, life + 12f); score += 50; Toast("STASH +12s");
            Destroy(s.gameObject); stashes.RemoveAt(i);
        }

        /// <summary>A crate smashed by hand comes apart into four planks you can pick up and throw.</summary>
        public void SmashCrate(Thing crate)
        {
            Vector3 c = crate.transform.position; Transform parent = crate.transform.parent;
            Material m = crate.GetComponent<Renderer>().sharedMaterial;
            Destroy(crate.gameObject);
            for (int k = 0; k < 4; k++)
            {
                var plank = Prop("Plank", c + new Vector3((k % 2 - 0.5f) * 0.4f, 0.1f + k * 0.12f, (k / 2 - 0.5f) * 0.4f), new Vector3(0.9f, 0.06f, 0.2f), m, 2f, parent);
                plank.transform.rotation = Quaternion.Euler(Random.Range(-20f, 20f), Random.Range(0f, 180f), Random.Range(-20f, 20f));
                plank.GetComponent<Rigidbody>().AddForce(Random.insideUnitSphere * 2.5f + Vector3.up * 2f, ForceMode.VelocityChange);
            }
            AddChaos(30, "SMASH");
        }

        public void OnPanelBroken(Panel p, Vector3 at)
        {
            int pts = MtlData.Points(p.mtl);
            score += pts; dollas += Mathf.Max(1, pts / 8); broken++;
            toast = (p.roof ? "CAVE-IN" : p.mtl == Mtl.Glass ? "SHATTER" : "SMASH") + " +" + pts; toastT = 1.2f;
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.R)) { Restart(); return; }
            toastT -= Time.deltaTime;
            if (Over || player == null) return;
            life -= Time.deltaTime;
            if (life <= 0f) { life = 0f; Over = true; Cursor.lockState = CursorLockMode.None; return; }
            Vector3 pp = player.transform.position;
            for (int i = stashes.Count - 1; i >= 0; i--)
            {
                var s = stashes[i];
                if (s == null) { stashes.RemoveAt(i); continue; }
                s.Rotate(0f, 90f * Time.deltaTime, 0f);
                s.position = new Vector3(s.position.x, 0.9f + Mathf.Sin(Time.time * 2.4f + i) * 0.12f, s.position.z);
                float dx = s.position.x - pp.x, dz = s.position.z - pp.z;
                if (dx * dx + dz * dz < 1.4f * 1.4f && Mathf.Abs(s.position.y - (pp.y + 0.9f)) < 1.6f) TakeStash(s);
            }
            if (stashes.Count < 4) { stashT -= Time.deltaTime; if (stashT <= 0f) { SpawnStash(); stashT = 3f; } }
        }

        void Restart()
        {
            if (World != null) Destroy(World.gameObject);
            stashes.Clear(); spots.Clear();
            life = 45f; score = 0; dollas = 0; broken = 0; Over = false; toast = "";
            BuildWorld();
            if (player != null) player.Respawn(new Vector3(0f, 0.2f, 4.5f));
        }

        static string Clock(float t) => t < 10f ? t.ToString("0.0") : $"{(int)(t / 60f)}:{(int)(t % 60f):00}";

        void OnGUI()
        {
            if (big == null)
            {
                big = new GUIStyle(GUI.skin.label) { fontSize = 40, fontStyle = FontStyle.Bold };
                small = new GUIStyle(GUI.skin.label) { fontSize = 18 };
                center = new GUIStyle(GUI.skin.label) { fontSize = 34, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            }
            float k = Screen.height / 720f;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(k, k, 1f));
            float w = Screen.width / k;
            GUI.Box(new Rect(12f, 10f, 250f, 100f), GUIContent.none);
            big.normal.textColor = life < 10f ? new Color(1f, 0.3f, 0.4f) : life < 15f ? new Color(1f, 0.71f, 0.24f) : new Color(0.49f, 1f, 0.6f);
            GUI.Label(new Rect(24f, 14f, 240f, 50f), Clock(life), big);
            GUI.Label(new Rect(24f, 66f, 240f, 30f), $"Chaos {score:N0} · Ð {dollas:N0} · {broken} smashed", small);
            if (toastT > 0f) GUI.Label(new Rect(0f, 120f, w, 44f), toast, center);
            GUI.Label(new Rect(16f, 720f - 34f, w - 32f, 30f), "WASD move · mouse look · Shift sprint · Space jump · Click/F tackle or throw · E/G use · X first person · R restart", small);
            if (Over)
            {
                GUI.Box(new Rect(w / 2f - 230f, 250f, 460f, 170f), GUIContent.none);
                GUI.Label(new Rect(w / 2f - 230f, 270f, 460f, 60f), "THE COMEDOWN WINS", center);
                GUI.Label(new Rect(w / 2f - 230f, 340f, 460f, 40f), $"Chaos {score:N0} · press R for another go", small);
            }
        }
    }
}
