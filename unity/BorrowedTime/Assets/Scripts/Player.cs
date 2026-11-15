using UnityEngine;

namespace BorrowedTime
{
    /// <summary>Third-person tweaker: walk, sprint, double jump, tackle. Walls take ½·m·v² damage when you hit them.</summary>
    [RequireComponent(typeof(CharacterController))]
    public class Player : MonoBehaviour
    {
        const float Walk = 5.8f, Sprint = 9.5f, JumpV = 8.4f, Gravity = 22f, TackleSpeed = 15f;
        CharacterController cc;
        Camera cam;
        Transform legL, legR, armL, armR, torso;
        float yaw, pitch = 18f, vy, tackleT, tackleCd, phase, camDist = 6.5f;
        bool doubleJump;
        Vector3 vel, tackleDir;

        public Vector3 Velocity => vel;

        void Start()
        {
            cc = GetComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = 0.34f; cc.center = new Vector3(0f, 0.875f, 0f); cc.stepOffset = 0.42f; cc.slopeLimit = 50f;
            cam = Camera.main;
            BuildBody();
        }

        GameObject Part(PrimitiveType type, Transform parent, Vector3 pos, Vector3 scale, Color col)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.layer = 2;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos; go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = Mat.Get(col, 0.2f);
            return go;
        }

        Transform Pivot(string name, Transform parent, Vector3 pos)
        {
            var p = new GameObject(name).transform; p.SetParent(parent, false); p.localPosition = pos; return p;
        }

        void BuildBody()
        {
            Color skin = Mat.Hex(0xe6c3a8), top = Mat.Hex(0x6f7350), pants = Mat.Hex(0x3e4a61), shoe = Mat.Hex(0xd8d4c8);
            torso = Pivot("Torso", transform, new Vector3(0f, 0.95f, 0f));
            Part(PrimitiveType.Capsule, torso, new Vector3(0f, 0.32f, 0f), new Vector3(0.46f, 0.36f, 0.3f), top);
            Part(PrimitiveType.Sphere, torso, new Vector3(0f, 0.82f, 0.02f), new Vector3(0.27f, 0.31f, 0.28f), skin);
            Part(PrimitiveType.Cube, torso, new Vector3(0f, 0.92f, -0.02f), new Vector3(0.29f, 0.1f, 0.3f), Mat.Hex(0xb8322c)); // cap
            legL = Pivot("LegL", transform, new Vector3(0.11f, 0.93f, 0f)); legR = Pivot("LegR", transform, new Vector3(-0.11f, 0.93f, 0f));
            foreach (var l in new[] { legL, legR })
            {
                Part(PrimitiveType.Capsule, l, new Vector3(0f, -0.45f, 0f), new Vector3(0.15f, 0.45f, 0.15f), pants);
                Part(PrimitiveType.Cube, l, new Vector3(0f, -0.9f, 0.06f), new Vector3(0.13f, 0.08f, 0.26f), shoe);
            }
            armL = Pivot("ArmL", torso, new Vector3(0.27f, 0.52f, 0f)); armR = Pivot("ArmR", torso, new Vector3(-0.27f, 0.52f, 0f));
            foreach (var a in new[] { armL, armR })
            {
                Part(PrimitiveType.Capsule, a, new Vector3(0f, -0.3f, 0f), new Vector3(0.12f, 0.3f, 0.12f), top);
                Part(PrimitiveType.Sphere, a, new Vector3(0f, -0.62f, 0f), new Vector3(0.1f, 0.1f, 0.1f), skin);
            }
        }

        public void Respawn(Vector3 at)
        {
            cc.enabled = false; transform.position = at; cc.enabled = true;
            vel = Vector3.zero; vy = 0f; tackleT = 0f;
        }

        void Update()
        {
            if (Game.I == null || Game.I.Over) return;
            if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked) { Cursor.lockState = CursorLockMode.Locked; return; }
            if (Input.GetKeyDown(KeyCode.Escape)) Cursor.lockState = CursorLockMode.None;
            yaw += Input.GetAxis("Mouse X") * 2.4f;
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * 2f, -10f, 70f);
            camDist = Mathf.Clamp(camDist - Input.mouseScrollDelta.y * 0.6f, 2.5f, 14f);

            Quaternion yr = Quaternion.Euler(0f, yaw, 0f);
            Vector3 fwd = yr * Vector3.forward, right = yr * Vector3.right, wish = Vector3.zero;
            if (Input.GetKey(KeyCode.W)) wish += fwd; if (Input.GetKey(KeyCode.S)) wish -= fwd;
            if (Input.GetKey(KeyCode.D)) wish += right; if (Input.GetKey(KeyCode.A)) wish -= right;
            if (wish.sqrMagnitude > 1f) wish.Normalize();

            tackleCd -= Time.deltaTime;
            bool tackle = Input.GetKeyDown(KeyCode.F) || (Input.GetMouseButtonDown(0) && Cursor.lockState == CursorLockMode.Locked);
            if (tackle && tackleCd <= 0f) { tackleT = 0.3f; tackleCd = 0.5f; tackleDir = wish.sqrMagnitude > 0.01f ? wish.normalized : fwd; }

            Vector3 horiz;
            if (tackleT > 0f) { tackleT -= Time.deltaTime; horiz = tackleDir * TackleSpeed; }
            else
            {
                Vector3 target = wish * (Input.GetKey(KeyCode.LeftShift) ? Sprint : Walk), cur = new Vector3(vel.x, 0f, vel.z);
                horiz = Vector3.MoveTowards(cur, target, (cc.isGrounded ? 48f : 15f) * Time.deltaTime);
            }
            if (cc.isGrounded)
            {
                doubleJump = true;
                if (vy < 0f) vy = -2f;
                if (Input.GetKeyDown(KeyCode.Space)) vy = JumpV;
            }
            else if (doubleJump && Input.GetKeyDown(KeyCode.Space)) { vy = 7.6f; doubleJump = false; }
            vy -= Gravity * (vy < 0f ? 1.25f : 1f) * Time.deltaTime;
            vel = new Vector3(horiz.x, vy, horiz.z);
            cc.Move(vel * Time.deltaTime);

            Vector3 flat = new Vector3(vel.x, 0f, vel.z);
            if (flat.sqrMagnitude > 0.5f) transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(flat), 12f * Time.deltaTime);
            Animate(flat.magnitude);
            if (transform.position.y < -20f) Respawn(new Vector3(0f, 1f, 4.5f));
        }

        void Animate(float speed)
        {
            phase += speed * Time.deltaTime * 1.7f;
            float a = Mathf.Clamp01(speed / 6f) * 40f, s = Mathf.Sin(phase);
            legL.localRotation = Quaternion.Euler(-a * s, 0f, 0f); legR.localRotation = Quaternion.Euler(a * s, 0f, 0f);
            float armRaise = tackleT > 0f ? -80f : 0f;
            armL.localRotation = Quaternion.Euler(a * s * 0.9f + armRaise, 0f, 8f); armR.localRotation = Quaternion.Euler(-a * s * 0.9f + armRaise, 0f, -8f);
            torso.localRotation = Quaternion.Euler(tackleT > 0f ? 30f : 4f + Mathf.Clamp01(speed / 9f) * 10f, 0f, 0f);
        }

        void LateUpdate()
        {
            if (cam == null) return;
            Vector3 target = transform.position + Vector3.up * 1.5f;
            Vector3 dir = Quaternion.Euler(pitch, yaw, 0f) * Vector3.back;
            float d = camDist;
            if (Physics.SphereCast(target, 0.2f, dir, out RaycastHit hit, camDist, ~(1 << 2), QueryTriggerInteraction.Ignore)) d = Mathf.Max(0.6f, hit.distance - 0.1f);
            cam.transform.position = target + dir * d;
            cam.transform.LookAt(target);
        }

        void OnControllerColliderHit(ControllerColliderHit hit)
        {
            float into = Vector3.Dot(vel, -hit.normal);
            var panel = hit.collider.GetComponent<Panel>();
            if (panel != null && into > 2.5f)
            {
                float mass = 75f * (tackleT > 0f ? 1.3f : 1f);
                bool broke = panel.Hit(0.5f * mass * into * into / 100f, hit.point, -hit.normal);
                if (!broke && tackleT > 0f) tackleT = 0f; // bounced off something too strong
            }
            var rb = hit.rigidbody;
            if (rb != null && !rb.isKinematic && into > 0.5f)
                rb.AddForceAtPosition(-hit.normal * into * Mathf.Min(rb.mass, 80f) * (tackleT > 0f ? 1.6f : 0.6f), hit.point, ForceMode.Impulse);
        }
    }
}
