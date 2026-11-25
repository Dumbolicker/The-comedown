// Borrowed Time engine: one sun with soft shadows, a sky/ground ambient, a little specular, and distance fog.

struct Globals {
    view_proj: mat4x4<f32>,
    light_view_proj: mat4x4<f32>,
    inv_view_proj: mat4x4<f32>,
    sun_dir: vec4<f32>,      // xyz: unit vector toward the sun
    sun_color: vec4<f32>,
    sky_top: vec4<f32>,
    sky_horizon: vec4<f32>,
    ground: vec4<f32>,
    camera_pos: vec4<f32>,
    fog: vec4<f32>,          // x: fog start, y: fog end (metres), z: shadow map texel size
};

@group(0) @binding(0) var<uniform> g: Globals;
@group(0) @binding(1) var shadow_map: texture_depth_2d;
@group(0) @binding(2) var shadow_sampler: sampler_comparison;

struct VIn {
    @location(0) pos: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) m0: vec4<f32>,
    @location(3) m1: vec4<f32>,
    @location(4) m2: vec4<f32>,
    @location(5) m3: vec4<f32>,
    @location(6) color: vec4<f32>,
};

struct VOut {
    @builtin(position) clip: vec4<f32>,
    @location(0) world: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) color: vec4<f32>,
    @location(3) light_clip: vec4<f32>,
};

fn model_of(v: VIn) -> mat4x4<f32> {
    return mat4x4<f32>(v.m0, v.m1, v.m2, v.m3);
}

@vertex
fn vs_main(v: VIn) -> VOut {
    let m = model_of(v);
    let world = m * vec4<f32>(v.pos, 1.0);
    // The model matrix is translation * rotation * scale, so the normal transform is rotation * (1 / scale).
    let s = vec3<f32>(length(v.m0.xyz), length(v.m1.xyz), length(v.m2.xyz));
    let rot = mat3x3<f32>(v.m0.xyz / s.x, v.m1.xyz / s.y, v.m2.xyz / s.z);
    var o: VOut;
    o.clip = g.view_proj * world;
    o.world = world.xyz;
    o.normal = normalize(rot * (v.normal / s));
    o.color = v.color;
    o.light_clip = g.light_view_proj * world;
    return o;
}

@vertex
fn vs_shadow(v: VIn) -> @builtin(position) vec4<f32> {
    return g.light_view_proj * model_of(v) * vec4<f32>(v.pos, 1.0);
}

fn sun_visibility(light_clip: vec4<f32>, n_dot_l: f32) -> f32 {
    let p = light_clip.xyz / light_clip.w;
    let uv = vec2<f32>(p.x * 0.5 + 0.5, -p.y * 0.5 + 0.5);
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0 || p.z > 1.0) {
        return 1.0;
    }
    let bias = mix(0.003, 0.0008, n_dot_l);
    let texel = g.fog.z;
    var lit = 0.0;
    for (var x = -1; x <= 1; x = x + 1) {
        for (var y = -1; y <= 1; y = y + 1) {
            lit = lit + textureSampleCompareLevel(shadow_map, shadow_sampler, uv + vec2<f32>(f32(x), f32(y)) * texel, p.z - bias);
        }
    }
    return lit / 9.0;
}

@fragment
fn fs_main(i: VOut) -> @location(0) vec4<f32> {
    let n = normalize(i.normal);
    let l = normalize(g.sun_dir.xyz);
    let n_dot_l = max(dot(n, l), 0.0);
    let lit = sun_visibility(i.light_clip, n_dot_l);
    let ambient = mix(g.ground.rgb, g.sky_top.rgb, n.y * 0.5 + 0.5);
    var rgb = i.color.rgb * (ambient * 0.55 + g.sun_color.rgb * n_dot_l * lit);
    let view = normalize(g.camera_pos.xyz - i.world);
    let h = normalize(l + view);
    rgb = rgb + g.sun_color.rgb * pow(max(dot(n, h), 0.0), 48.0) * 0.10 * lit;
    let d = distance(g.camera_pos.xyz, i.world);
    let f = clamp((d - g.fog.x) / (g.fog.y - g.fog.x), 0.0, 1.0);
    return vec4<f32>(mix(rgb, g.sky_horizon.rgb, f * f), 1.0);
}

struct SkyOut {
    @builtin(position) clip: vec4<f32>,
    @location(0) ndc: vec2<f32>,
};

@vertex
fn vs_sky(@builtin(vertex_index) vi: u32) -> SkyOut {
    let uv = vec2<f32>(f32((vi << 1u) & 2u), f32(vi & 2u));
    let p = uv * 2.0 - 1.0;
    var o: SkyOut;
    o.clip = vec4<f32>(p, 0.0, 1.0);
    o.ndc = p;
    return o;
}

@fragment
fn fs_sky(i: SkyOut) -> @location(0) vec4<f32> {
    let far = g.inv_view_proj * vec4<f32>(i.ndc, 1.0, 1.0);
    let dir = normalize(far.xyz / far.w - g.camera_pos.xyz);
    var c = mix(g.sky_horizon.rgb, g.sky_top.rgb, clamp(dir.y * 2.5, 0.0, 1.0));
    let s = max(dot(dir, normalize(g.sun_dir.xyz)), 0.0);
    c = c + g.sun_color.rgb * pow(s, 800.0) * 1.5;
    return vec4<f32>(c, 1.0);
}
