//! Physics: a thin layer over Rapier that steps at a fixed 60 Hz and reports how hard things hit each other.

use std::sync::mpsc::{Receiver, channel};

use rapier3d::prelude::*;

pub use rapier3d::glamx::{Mat4, Quat, Vec3};
pub use rapier3d::prelude::{ColliderHandle, ImpulseJointHandle, RigidBodyHandle, RigidBodyType as BodyType};

/// The fixed simulation step, in seconds.
pub const DT: f32 = 1.0 / 60.0;
/// Earth's standard gravity, m/s².
pub const GRAVITY: f32 = 9.81;

/// One contact from the last step: the two colliders and the impulse between them (N·s).
#[derive(Clone, Copy, Debug)]
pub struct Impact {
    pub collider1: ColliderHandle,
    pub collider2: ColliderHandle,
    pub impulse: f32,
}

/// The physics world. Call [`Physics::advance`] with real elapsed time; it runs whole fixed steps.
pub struct Physics {
    pub world: PhysicsWorld,
    events: ChannelEventCollector,
    collisions: Receiver<CollisionEvent>,
    forces: Receiver<ContactForceEvent>,
    accumulator: f32,
    /// Contacts reported during the most recent step (only colliders that ask for force events).
    pub impacts: Vec<Impact>,
    /// Simulated time so far, in seconds.
    pub time: f32,
}

impl Default for Physics {
    fn default() -> Self {
        Self::new()
    }
}

impl Physics {
    pub fn new() -> Self {
        let (collision_tx, collisions) = channel();
        let (force_tx, forces) = channel();
        let (tear_tx, _tears) = channel();
        let mut world = PhysicsWorld::new();
        world.gravity = Vec3::new(0.0, -GRAVITY, 0.0);
        world.integration_parameters.dt = DT;
        Self {
            world,
            events: ChannelEventCollector::new(collision_tx, force_tx, tear_tx),
            collisions,
            forces,
            accumulator: 0.0,
            impacts: Vec::new(),
            time: 0.0,
        }
    }

    /// Runs one fixed step and collects the impacts it produced.
    pub fn step(&mut self) {
        self.world.step_with_events(&(), &self.events);
        self.time += DT;
        self.impacts.clear();
        while let Ok(ev) = self.forces.try_recv() {
            self.impacts.push(Impact { collider1: ev.collider1, collider2: ev.collider2, impulse: ev.total_force_magnitude * DT });
        }
        while self.collisions.try_recv().is_ok() {}
    }

    /// Adds real elapsed time and runs as many fixed steps as fit (at most 8, so a stall can't snowball).
    /// Returns how many steps ran; `step` handlers that care about every step should use [`Physics::step`].
    pub fn advance(&mut self, seconds: f32) -> usize {
        self.accumulator = (self.accumulator + seconds).min(8.0 * DT);
        let mut n = 0;
        while self.accumulator >= DT {
            self.step();
            self.accumulator -= DT;
            n += 1;
        }
        n
    }

    /// A flat, fixed ground whose top is at y = 0.
    pub fn add_ground(&mut self, half_extent: f32) -> ColliderHandle {
        let collider = ColliderBuilder::cuboid(half_extent, 0.5, half_extent).translation(Vec3::new(0.0, -0.5, 0.0)).friction(0.9);
        self.world.insert_collider(collider, None)
    }

    /// A dynamic box. `density` is in kg/m³ (pine is about 500, water 1000).
    pub fn add_box(&mut self, center: Vec3, half: Vec3, density: f32) -> (RigidBodyHandle, ColliderHandle) {
        let body = RigidBodyBuilder::dynamic().translation(center).ccd_enabled(true);
        let collider = ColliderBuilder::cuboid(half.x, half.y, half.z)
            .density(density)
            .friction(0.7)
            .restitution(0.1)
            .active_events(ActiveEvents::CONTACT_FORCE_EVENTS)
            .contact_force_event_threshold(1.0);
        self.world.insert(body, collider)
    }

    /// A dynamic ball.
    pub fn add_ball(&mut self, center: Vec3, radius: f32, density: f32) -> (RigidBodyHandle, ColliderHandle) {
        let body = RigidBodyBuilder::dynamic().translation(center).ccd_enabled(true);
        let collider = ColliderBuilder::ball(radius)
            .density(density)
            .friction(0.6)
            .restitution(0.3)
            .active_events(ActiveEvents::CONTACT_FORCE_EVENTS)
            .contact_force_event_threshold(1.0);
        self.world.insert(body, collider)
    }

    /// A fixed (immovable until told otherwise) box, such as a wall panel.
    pub fn add_fixed_box(&mut self, center: Vec3, half: Vec3, density: f32) -> (RigidBodyHandle, ColliderHandle) {
        let body = RigidBodyBuilder::fixed().translation(center);
        let collider = ColliderBuilder::cuboid(half.x, half.y, half.z)
            .density(density)
            .friction(0.8)
            .active_events(ActiveEvents::CONTACT_FORCE_EVENTS)
            .contact_force_event_threshold(1.0);
        self.world.insert(body, collider)
    }

    pub fn pose(&self, body: RigidBodyHandle) -> (Vec3, Quat) {
        let b = &self.world.bodies[body];
        (b.translation(), *b.rotation())
    }

    pub fn velocity(&self, body: RigidBodyHandle) -> Vec3 {
        self.world.bodies[body].linvel()
    }

    pub fn mass(&self, body: RigidBodyHandle) -> f32 {
        self.world.bodies[body].mass()
    }

    pub fn set_velocity(&mut self, body: RigidBodyHandle, v: Vec3) {
        self.world.bodies[body].set_linvel(v, true);
    }

    /// The body a collider is attached to, if any.
    pub fn body_of(&self, collider: ColliderHandle) -> Option<RigidBodyHandle> {
        self.world.colliders.get(collider).and_then(|c| c.parent())
    }

    pub fn remove_body(&mut self, body: RigidBodyHandle) {
        self.world.remove_body_with_colliders(body, true);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A ball dropped from 20 m: the fall time should match h = g t² / 2 (t = 2.019 s), so the measured g ≈ 9.81.
    #[test]
    fn free_fall_matches_gravity() {
        let mut p = Physics::new();
        p.add_ground(50.0);
        let (ball, _) = p.add_ball(Vec3::new(0.0, 20.0 + 0.25, 0.0), 0.25, 500.0);
        let mut steps = 0;
        while p.pose(ball).0.y > 0.25 + 0.01 && steps < 1000 {
            p.step();
            steps += 1;
        }
        let t = steps as f32 * DT;
        let g = 2.0 * 20.0 / (t * t);
        let err = (g - GRAVITY).abs() / GRAVITY;
        println!("free fall: 20 m in {t:.3} s, measured g = {g:.2} m/s², {:.1}% off", err * 100.0);
        assert!(err < 0.02, "measured g {g} is more than 2% off");
    }

    /// A 30 kg box thrown at a fixed wall reports an impulse close to m·Δv.
    #[test]
    fn impacts_report_impulse() {
        let mut p = Physics::new();
        p.add_ground(50.0);
        p.add_fixed_box(Vec3::new(0.0, 1.0, 3.0), Vec3::new(1.0, 1.0, 0.1), 500.0);
        let (crate_, _) = p.add_box(Vec3::new(0.0, 1.0, 0.0), Vec3::splat(0.25), 30.0 / 0.125);
        p.set_velocity(crate_, Vec3::new(0.0, 0.0, 10.0));
        let mut total = 0.0;
        for _ in 0..60 {
            p.step();
            total += p.impacts.iter().map(|i| i.impulse).sum::<f32>();
            if p.velocity(crate_).z <= 0.5 {
                break;
            }
        }
        let m = p.mass(crate_);
        println!("box of {m:.1} kg at 10 m/s: wall impulse {total:.0} N·s (m·v = {:.0})", m * 10.0);
        assert!((m - 30.0).abs() < 0.5);
        assert!(total > 0.6 * m * 10.0, "impulse {total} too small");
    }
}
