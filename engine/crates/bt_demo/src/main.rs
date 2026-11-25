//! Headless demo of the Borrowed Time engine: a street corner with a wood house front, a shop window and a brick wall.
//! A body gets knocked into the house, a crate goes through the window and a heavy ball into the bricks. Renders frames
//! to PNG and prints what broke and how long the physics and the renderer took.
//!
//! Usage: bt_demo [out-dir] [width height]

use std::time::Instant;

use bt_engine::destruct::{self, Wall};
use bt_engine::physics::{BodyType, Physics, Quat, RigidBodyHandle, Vec3};
use bt_engine::ragdoll::{PartShape, Ragdoll};
use bt_engine::render::{Camera, DrawItem, Renderer, Shape};

/// sRGB hex colour to linear RGBA (the renderer lights in linear space).
fn rgb(hex: u32) -> [f32; 4] {
    let c = |v: u32| {
        let s = v as f32 / 255.0;
        if s <= 0.04045 { s / 12.92 } else { ((s + 0.055) / 1.055).powf(2.4) }
    };
    [c((hex >> 16) & 255), c((hex >> 8) & 255), c(hex & 255), 1.0]
}

struct Thing {
    body: RigidBodyHandle,
    shape: Shape,
    scale: Vec3,
    color: [f32; 4],
}

struct Scene {
    physics: Physics,
    walls: Vec<(Wall, [f32; 4])>,
    things: Vec<Thing>,
    ragdoll: Ragdoll,
    log: Vec<String>,
}

impl Scene {
    fn new() -> Self {
        let mut physics = Physics::new();
        physics.add_ground(60.0);
        let house = Wall::new(&mut physics, Vec3::new(-3.0, 0.0, 6.0), 6, 3, (1.0, 1.0), 0.12, destruct::WOOD);
        let window = Wall::new(&mut physics, Vec3::new(4.0, 0.0, 3.0), 3, 2, (1.0, 1.0), 0.03, destruct::GLASS);
        let bricks = Wall::new(&mut physics, Vec3::new(-9.0, 0.0, 3.5), 4, 3, (1.0, 0.75), 0.25, destruct::BRICK);
        let mut ragdoll = Ragdoll::spawn(&mut physics, Vec3::new(0.0, 0.0, 3.4));
        ragdoll.set_strength(&mut physics, 0.6);
        // hold the body upright until something hits it
        let pelvis = ragdoll.part("pelvis").unwrap().body;
        physics.world.bodies[pelvis].set_body_type(BodyType::KinematicPositionBased, true);
        let mut things = Vec::new();
        for (i, y) in [0.3_f32, 0.9, 1.5].iter().enumerate() {
            let (body, _) = physics.add_box(Vec3::new(-6.5 + 0.05 * i as f32, *y, 1.2), Vec3::splat(0.3), 25.0 / 0.216);
            things.push(Thing { body, shape: Shape::Box, scale: Vec3::splat(0.6), color: rgb(0xb88a55) });
        }
        let walls = vec![(house, rgb(0xe9d6b4)), (window, [0.55, 0.75, 0.9, 1.0]), (bricks, rgb(0xa5503c))];
        Self { physics, walls, things, ragdoll, log: Vec::new() }
    }

    fn throw(&mut self, at: Vec3, velocity: Vec3, ball: Option<(f32, f32)>, color: u32, what: &str) {
        let (body, shape, scale) = match ball {
            Some((radius, density)) => {
                let (b, _) = self.physics.add_ball(at, radius, density);
                (b, Shape::Ball, Vec3::splat(radius * 2.0))
            }
            None => {
                let (b, _) = self.physics.add_box(at, Vec3::splat(0.25), 30.0 / 0.125);
                (b, Shape::Box, Vec3::splat(0.5))
            }
        };
        self.physics.set_velocity(body, velocity);
        let m = self.physics.mass(body);
        self.log.push(format!("t={:.2}s threw {what}: {m:.0} kg at {:.1} m/s ({:.0} J)", self.physics.time, velocity.length(), 0.5 * m * velocity.length_squared()));
        self.things.push(Thing { body, shape, scale, color: rgb(color) });
    }

    fn step(&mut self) {
        self.physics.step();
        let t = self.physics.time;
        for (wall, color) in &mut self.walls {
            let report = wall.update(&mut self.physics);
            for &i in &report.broken {
                let p = &wall.panels[i];
                self.log.push(format!("t={t:.2}s broke a {} panel (row {}, col {}) after {:.0} J", p.material.name, p.row, p.col, p.damage));
            }
            if !report.started_falling.is_empty() {
                self.log.push(format!("t={t:.2}s {} panel(s) lost their support and fell", report.started_falling.len()));
            }
            for c in report.chunks {
                self.things.push(Thing { body: c.body, shape: Shape::Box, scale: c.half * 2.0, color: *color });
            }
        }
    }

    fn draw_items(&self) -> Vec<DrawItem> {
        let mut items = vec![
            DrawItem { shape: Shape::Box, position: Vec3::new(0.0, -0.05, 0.0), rotation: Quat::IDENTITY, scale: Vec3::new(120.0, 0.1, 120.0), color: rgb(0x6f9a4f) },
            DrawItem { shape: Shape::Box, position: Vec3::new(0.0, -0.04, -2.0), rotation: Quat::IDENTITY, scale: Vec3::new(120.0, 0.1, 7.0), color: rgb(0x3a3a42) },
            DrawItem { shape: Shape::Box, position: Vec3::new(0.0, -0.03, 1.8), rotation: Quat::IDENTITY, scale: Vec3::new(120.0, 0.1, 1.6), color: rgb(0xb5b0a6) },
        ];
        for (wall, color) in &self.walls {
            for p in wall.panels.iter().filter(|p| p.state != destruct::State::Broken) {
                let (pos, rot) = self.physics.pose(p.body);
                items.push(DrawItem { shape: Shape::Box, position: pos, rotation: rot, scale: p.half * 2.0, color: *color });
            }
        }
        for t in &self.things {
            if self.physics.world.bodies.get(t.body).is_none() {
                continue;
            }
            let (pos, rot) = self.physics.pose(t.body);
            items.push(DrawItem { shape: t.shape, position: pos, rotation: rot, scale: t.scale, color: t.color });
        }
        let skin = rgb(0xe2b896);
        for part in &self.ragdoll.parts {
            let (pos, rot) = self.physics.pose(part.body);
            let color = match part.name {
                "head" => skin,
                n if n.starts_with("forearm") => skin,
                n if n.starts_with("shin") || n.starts_with("thigh") || n == "pelvis" => rgb(0x3e4a61),
                _ => rgb(0x6f7350),
            };
            let (shape, scale) = match part.shape {
                PartShape::Box(h) => (Shape::Box, h * 2.0),
                PartShape::Ball(r) => (Shape::Ball, Vec3::splat(r * 2.0)),
                PartShape::Capsule { half_height, radius } => (Shape::Capsule { half_height, radius }, Vec3::ONE),
            };
            items.push(DrawItem { shape, position: pos, rotation: rot, scale, color });
        }
        items
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let out = std::path::PathBuf::from(args.get(1).map(String::as_str).unwrap_or("engine-shots"));
    let (w, h) = match (args.get(2), args.get(3)) {
        (Some(w), Some(h)) => (w.parse().unwrap_or(960), h.parse().unwrap_or(540)),
        _ => (960, 540),
    };
    std::fs::create_dir_all(&out).expect("output folder");

    let t0 = Instant::now();
    let mut renderer = match Renderer::new_headless(w, h) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("Can't render here: {e}");
            std::process::exit(2);
        }
    };
    println!("renderer: {} at {w}x{h} (started in {:.0} ms)", renderer.adapter(), t0.elapsed().as_secs_f64() * 1000.0);

    let mut scene = Scene::new();
    let camera = Camera { eye: Vec3::new(6.5, 4.2, -7.5), target: Vec3::new(-0.5, 1.0, 3.5), fov_y: 55f32.to_radians() };
    let shots = [0.10_f32, 0.75, 1.35, 3.0];
    let mut next = 0;
    let (mut physics_ms, mut steps, mut render_ms, mut frames) = (0.0, 0, 0.0, 0);
    let mut hit_body = false;
    while next < shots.len() {
        let t = scene.physics.time;
        if (t - 0.30).abs() < 0.008 {
            // a heavy ball knocks the body into the house
            scene.throw(Vec3::new(3.0, 1.2, 3.4), Vec3::new(-14.0, 0.5, 1.0), Some((0.3, 1500.0)), 0x2f2f33, "a 170 kg ball at the body");
        }
        if (t - 0.40).abs() < 0.008 {
            scene.throw(Vec3::new(5.5, 1.0, 0.0), Vec3::new(0.0, 1.5, 11.0), None, 0xb88a55, "a crate at the shop window");
        }
        if (t - 0.55).abs() < 0.008 {
            scene.throw(Vec3::new(-7.0, 1.0, -2.0), Vec3::new(0.0, 1.0, 16.0), Some((0.35, 7800.0)), 0x55585e, "a steel ball at the brick wall");
        }
        if !hit_body && scene.ragdoll.max_speed(&scene.physics) > 0.5 || (!hit_body && t > 0.45) {
            let pelvis = scene.ragdoll.part("pelvis").unwrap().body;
            scene.physics.world.bodies[pelvis].set_body_type(BodyType::Dynamic, true);
            scene.ragdoll.set_strength(&mut scene.physics, 0.15);
            hit_body = true;
        }
        let s = Instant::now();
        scene.step();
        physics_ms += s.elapsed().as_secs_f64() * 1000.0;
        steps += 1;
        if scene.physics.time >= shots[next] {
            let items = scene.draw_items();
            let s = Instant::now();
            let img = renderer.render(&camera, &items);
            render_ms += s.elapsed().as_secs_f64() * 1000.0;
            frames += 1;
            let path = out.join(format!("frame_{}.png", next + 1));
            img.save(&path).expect("save png");
            println!("t={:.2}s: {} things drawn -> {}", scene.physics.time, items.len(), path.display());
            next += 1;
        }
    }
    for line in &scene.log {
        println!("{line}");
    }
    let standing: usize = scene.walls.iter().map(|(w, _)| w.standing()).sum();
    let total: usize = scene.walls.iter().map(|(w, _)| w.panels.len()).sum();
    println!("panels standing: {standing} of {total}; rigid bodies: {}", scene.physics.world.bodies.len());
    println!("physics: {steps} steps, {:.3} ms per step on average", physics_ms / steps as f64);
    println!("render: {frames} frames, {:.0} ms per frame on average ({})", render_ms / frames as f64, renderer.adapter());
}
