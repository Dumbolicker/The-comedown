//! A jointed body (an "active ragdoll"): eleven rigid parts held together by ball joints with human-ish limits,
//! plus joint motors that pull each joint back toward its rest pose. Motor strength 1 holds a pose, 0 is a limp flop.
//!
//! Proportions follow average adult anthropometry (a 1.75 m, 75 kg person): segment lengths and masses are fractions
//! of height and body mass, after Winter, "Biomechanics and Motor Control of Human Movement" (4th ed., 2009), table 4.1.

use rapier3d::prelude::*;

use crate::physics::{Physics, Quat, RigidBodyHandle, Vec3};

/// A body part: its rigid body, collider shape (for drawing) and name.
#[derive(Clone, Copy, Debug)]
pub struct Part {
    pub name: &'static str,
    pub body: RigidBodyHandle,
    pub shape: PartShape,
}

#[derive(Clone, Copy, Debug)]
pub enum PartShape {
    /// Half extents of a box.
    Box(Vec3),
    /// A capsule along the part's local Y axis: half height of the straight section and radius.
    Capsule { half_height: f32, radius: f32 },
    Ball(f32),
}

pub struct Ragdoll {
    pub parts: Vec<Part>,
    /// Each joint with its parent and child bodies.
    pub joints: Vec<(ImpulseJointHandle, RigidBodyHandle, RigidBodyHandle)>,
    strength: f32,
}

/// Total mass of the person, kg.
pub const MASS: f32 = 75.0;

struct Spec {
    name: &'static str,
    shape: PartShape,
    center: Vec3,
    mass_fraction: f32,
}

impl Ragdoll {
    /// Builds the body standing with its feet on y = `feet.y`.
    pub fn spawn(physics: &mut Physics, feet: Vec3) -> Self {
        // (name, shape, center relative to the feet, share of body mass)
        let specs = [
            Spec { name: "pelvis", shape: PartShape::Box(Vec3::new(0.16, 0.09, 0.10)), center: Vec3::new(0.0, 0.98, 0.0), mass_fraction: 0.142 },
            Spec { name: "chest", shape: PartShape::Box(Vec3::new(0.18, 0.22, 0.11)), center: Vec3::new(0.0, 1.31, 0.0), mass_fraction: 0.355 },
            Spec { name: "head", shape: PartShape::Ball(0.11), center: Vec3::new(0.0, 1.66, 0.0), mass_fraction: 0.081 },
            Spec { name: "upper arm L", shape: PartShape::Capsule { half_height: 0.10, radius: 0.05 }, center: Vec3::new(0.25, 1.36, 0.0), mass_fraction: 0.028 },
            Spec { name: "upper arm R", shape: PartShape::Capsule { half_height: 0.10, radius: 0.05 }, center: Vec3::new(-0.25, 1.36, 0.0), mass_fraction: 0.028 },
            Spec { name: "forearm L", shape: PartShape::Capsule { half_height: 0.10, radius: 0.04 }, center: Vec3::new(0.25, 1.06, 0.0), mass_fraction: 0.022 },
            Spec { name: "forearm R", shape: PartShape::Capsule { half_height: 0.10, radius: 0.04 }, center: Vec3::new(-0.25, 1.06, 0.0), mass_fraction: 0.022 },
            Spec { name: "thigh L", shape: PartShape::Capsule { half_height: 0.15, radius: 0.07 }, center: Vec3::new(0.10, 0.68, 0.0), mass_fraction: 0.100 },
            Spec { name: "thigh R", shape: PartShape::Capsule { half_height: 0.15, radius: 0.07 }, center: Vec3::new(-0.10, 0.68, 0.0), mass_fraction: 0.100 },
            Spec { name: "shin L", shape: PartShape::Capsule { half_height: 0.15, radius: 0.055 }, center: Vec3::new(0.10, 0.25, 0.0), mass_fraction: 0.061 },
            Spec { name: "shin R", shape: PartShape::Capsule { half_height: 0.15, radius: 0.055 }, center: Vec3::new(-0.10, 0.25, 0.0), mass_fraction: 0.061 },
        ];
        let mut parts = Vec::with_capacity(specs.len());
        for s in &specs {
            let mass = MASS * s.mass_fraction;
            let collider = match s.shape {
                PartShape::Box(h) => ColliderBuilder::cuboid(h.x, h.y, h.z),
                PartShape::Capsule { half_height, radius } => ColliderBuilder::capsule_y(half_height, radius),
                PartShape::Ball(r) => ColliderBuilder::ball(r),
            }
            .mass(mass)
            .friction(0.8)
            .active_events(ActiveEvents::CONTACT_FORCE_EVENTS)
            .contact_force_event_threshold(1.0);
            let body = RigidBodyBuilder::dynamic()
                .translation(feet + s.center)
                .linear_damping(0.05)
                .angular_damping(0.4)
                .ccd_enabled(true);
            let (body, _) = physics.world.insert(body, collider);
            parts.push(Part { name: s.name, body, shape: s.shape });
        }
        let idx = |name: &str| parts.iter().position(|p| p.name == name).unwrap();
        // (parent, child, joint position relative to the feet, swing limit in radians, twist limit)
        let links = [
            ("pelvis", "chest", Vec3::new(0.0, 1.08, 0.0), 0.6, 0.5),
            ("chest", "head", Vec3::new(0.0, 1.55, 0.0), 0.7, 0.9),
            ("chest", "upper arm L", Vec3::new(0.25, 1.48, 0.0), 1.8, 1.2),
            ("chest", "upper arm R", Vec3::new(-0.25, 1.48, 0.0), 1.8, 1.2),
            ("upper arm L", "forearm L", Vec3::new(0.25, 1.21, 0.0), 1.4, 0.3),
            ("upper arm R", "forearm R", Vec3::new(-0.25, 1.21, 0.0), 1.4, 0.3),
            ("pelvis", "thigh L", Vec3::new(0.10, 0.88, 0.0), 1.3, 0.5),
            ("pelvis", "thigh R", Vec3::new(-0.10, 0.88, 0.0), 1.3, 0.5),
            ("thigh L", "shin L", Vec3::new(0.10, 0.47, 0.0), 1.4, 0.2),
            ("thigh R", "shin R", Vec3::new(-0.10, 0.47, 0.0), 1.4, 0.2),
        ];
        let mut joints = Vec::with_capacity(links.len());
        for (parent, child, at, swing, twist) in links {
            let (p, c) = (parts[idx(parent)].body, parts[idx(child)].body);
            let (pp, _) = physics.pose(p);
            let (cp, _) = physics.pose(c);
            let joint = SphericalJointBuilder::new()
                .local_anchor1(feet + at - pp)
                .local_anchor2(feet + at - cp)
                .contacts_enabled(false)
                .limits(JointAxis::AngX, [-swing, swing])
                .limits(JointAxis::AngZ, [-swing, swing])
                .limits(JointAxis::AngY, [-twist, twist]);
            joints.push((physics.world.insert_impulse_joint(p, c, joint), p, c));
        }
        let mut ragdoll = Self { parts, joints, strength: 0.0 };
        ragdoll.set_strength(physics, 1.0);
        ragdoll
    }

    /// Muscle tone, 0 (limp) to 1 (holds its pose against gravity's pull on the limbs).
    pub fn set_strength(&mut self, physics: &mut Physics, strength: f32) {
        self.strength = strength.clamp(0.0, 1.0);
        // Stiffness in N·m/rad and damping in N·m·s/rad, scaled by the mass of the limbs a joint holds up.
        let stiffness = 600.0 * self.strength;
        let damping = 40.0 * self.strength + 2.0;
        for &(j, _, _) in &self.joints {
            if let Some(joint) = physics.world.impulse_joints.get_mut(j, true) {
                for axis in [JointAxis::AngX, JointAxis::AngY, JointAxis::AngZ] {
                    joint.data.set_motor_position(axis, 0.0, stiffness, damping);
                }
            }
        }
    }

    pub fn strength(&self) -> f32 {
        self.strength
    }

    pub fn part(&self, name: &str) -> Option<&Part> {
        self.parts.iter().find(|p| p.name == name)
    }

    /// Pushes every part with the same velocity change (a shove, a car, an explosion).
    pub fn launch(&self, physics: &mut Physics, velocity: Vec3) {
        for p in &self.parts {
            let b = &mut physics.world.bodies[p.body];
            let v = b.linvel() + velocity;
            b.set_linvel(v, true);
        }
    }

    /// The largest distance between the two sides of any joint, in metres: how far the body has come apart.
    pub fn max_joint_gap(&self, physics: &Physics) -> f32 {
        let mut worst: f32 = 0.0;
        for &(j, body1, body2) in &self.joints {
            let Some(joint) = physics.world.impulse_joints.get(j) else { continue };
            let a1 = physics.world.bodies[body1].position().transform_point(joint.data.local_anchor1());
            let a2 = physics.world.bodies[body2].position().transform_point(joint.data.local_anchor2());
            worst = worst.max((a1 - a2).length());
        }
        worst
    }

    /// The highest speed of any part, m/s.
    pub fn max_speed(&self, physics: &Physics) -> f32 {
        self.parts.iter().map(|p| physics.velocity(p.body).length()).fold(0.0, f32::max)
    }

    pub fn pose_of(&self, physics: &Physics, name: &str) -> Option<(Vec3, Quat)> {
        self.part(name).map(|p| physics.pose(p.body))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A limp body dropped from 2 m lands, stays in one piece and comes to rest.
    #[test]
    fn limp_ragdoll_settles_in_one_piece() {
        let mut p = Physics::new();
        p.add_ground(50.0);
        let mut r = Ragdoll::spawn(&mut p, Vec3::new(0.0, 2.0, 0.0));
        r.set_strength(&mut p, 0.0);
        r.launch(&mut p, Vec3::new(1.5, 0.0, 0.5));
        let mut worst_gap: f32 = 0.0;
        for _ in 0..(6.0 / crate::physics::DT) as usize {
            p.step();
            worst_gap = worst_gap.max(r.max_joint_gap(&p));
        }
        let speed = r.max_speed(&p);
        let total_mass: f32 = r.parts.iter().map(|part| p.mass(part.body)).sum();
        let lowest = r.parts.iter().map(|part| p.pose(part.body).0.y).fold(f32::MAX, f32::min);
        println!("limp drop: {total_mass:.1} kg, worst joint gap {:.1} mm, fastest part after 6 s {speed:.3} m/s, lowest part y {lowest:.2} m",
                 worst_gap * 1000.0);
        assert!((total_mass - MASS).abs() < 0.5);
        assert!(worst_gap < 0.05, "joints opened by {worst_gap} m");
        assert!(speed < 0.2, "still moving at {speed} m/s");
        assert!(lowest > -0.05, "fell through the ground");
    }

    /// With full strength the joints hold: the head stays above the pelvis while the body is held upright.
    #[test]
    fn strong_ragdoll_holds_its_shape() {
        let mut p = Physics::new();
        p.add_ground(50.0);
        let r = Ragdoll::spawn(&mut p, Vec3::new(0.0, 0.0, 0.0));
        // pin the pelvis so only the joints are tested, not balance
        let pelvis = r.part("pelvis").unwrap().body;
        p.world.bodies[pelvis].set_body_type(RigidBodyType::KinematicPositionBased, true);
        for _ in 0..120 {
            p.step();
        }
        let (head, _) = r.pose_of(&p, "head").unwrap();
        let (hand, _) = r.pose_of(&p, "forearm L").unwrap();
        println!("held pose after 2 s: head at {:.2} m (rest 1.66), left forearm at {:.2} m (rest 1.06)", head.y, hand.y);
        assert!(head.y > 1.55, "head sagged to {}", head.y);
        assert!(hand.y > 0.9, "arm sagged to {}", hand.y);
    }
}
