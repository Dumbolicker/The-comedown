//! Breakable walls. A wall is a grid of panels that stand still (fixed bodies) until something hits them hard enough.
//! Each hit delivers kinetic energy E = J² / 2m (J: the contact impulse, m: the mass of what hit it). A panel breaks
//! into chunks once the energy adds up to its strength. Any standing panel left with nothing under it starts to fall.

use rapier3d::prelude::*;

use crate::physics::{ColliderHandle, Physics, RigidBodyHandle, Vec3};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Material {
    pub name: &'static str,
    /// kg/m³
    pub density: f32,
    /// Energy that breaks a 1 m² panel, in joules. Thicker or bigger panels scale with their area.
    pub strength: f32,
    /// Size of the pieces it breaks into, in metres.
    pub chunk: f32,
}

/// Wood framing and siding.
pub const WOOD: Material = Material { name: "wood", density: 500.0, strength: 900.0, chunk: 0.5 };
/// Window glass.
pub const GLASS: Material = Material { name: "glass", density: 2500.0, strength: 60.0, chunk: 0.25 };
/// Brick and mortar.
pub const BRICK: Material = Material { name: "brick", density: 1900.0, strength: 4000.0, chunk: 0.35 };

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum State {
    Standing,
    Falling,
    Broken,
}

#[derive(Clone, Debug)]
pub struct Panel {
    pub body: RigidBodyHandle,
    pub collider: ColliderHandle,
    pub center: Vec3,
    pub half: Vec3,
    pub col: usize,
    pub row: usize,
    pub material: Material,
    pub damage: f32,
    pub strength: f32,
    pub state: State,
}

/// A chunk left over from a broken panel.
#[derive(Clone, Copy, Debug)]
pub struct Chunk {
    pub body: RigidBodyHandle,
    pub half: Vec3,
    pub material: Material,
}

/// What happened to a wall during one update.
#[derive(Clone, Debug, Default)]
pub struct Report {
    pub broken: Vec<usize>,
    pub started_falling: Vec<usize>,
    pub chunks: Vec<Chunk>,
}

pub struct Wall {
    pub panels: Vec<Panel>,
    pub cols: usize,
    pub rows: usize,
}

impl Wall {
    /// A wall `cols` × `rows` panels of `panel` size (width, height) and `thickness`, standing on y = 0, running
    /// along X from `origin` (its bottom-left-front corner, at its centerline in Z).
    pub fn new(physics: &mut Physics, origin: Vec3, cols: usize, rows: usize, panel: (f32, f32), thickness: f32, material: Material) -> Self {
        let mut panels = Vec::with_capacity(cols * rows);
        let half = Vec3::new(panel.0 * 0.5, panel.1 * 0.5, thickness * 0.5);
        for row in 0..rows {
            for col in 0..cols {
                let center = origin + Vec3::new((col as f32 + 0.5) * panel.0, (row as f32 + 0.5) * panel.1, 0.0);
                let (body, collider) = physics.add_fixed_box(center, half * 0.999, material.density);
                panels.push(Panel {
                    body,
                    collider,
                    center,
                    half,
                    col,
                    row,
                    material,
                    damage: 0.0,
                    strength: material.strength * panel.0 * panel.1,
                    state: State::Standing,
                });
            }
        }
        Self { panels, cols, rows }
    }

    pub fn standing(&self) -> usize {
        self.panels.iter().filter(|p| p.state == State::Standing).count()
    }

    /// Reads the last step's impacts, breaks panels that took enough energy and drops the ones left unsupported.
    pub fn update(&mut self, physics: &mut Physics) -> Report {
        let mut report = Report::default();
        // energy delivered to each standing panel this step
        let impacts = physics.impacts.clone();
        for imp in &impacts {
            for (mine, other) in [(imp.collider1, imp.collider2), (imp.collider2, imp.collider1)] {
                let Some(i) = self.panels.iter().position(|p| p.collider == mine && p.state == State::Standing) else { continue };
                let Some(body) = physics.body_of(other) else { continue };
                let b = &physics.world.bodies[body];
                if !b.is_dynamic() {
                    continue;
                }
                let m = b.mass().max(0.1);
                self.panels[i].damage += imp.impulse * imp.impulse / (2.0 * m);
                if self.panels[i].damage >= self.panels[i].strength {
                    let dir = b.linvel().normalize_or_zero();
                    report.chunks.extend(self.shatter(physics, i, dir));
                    report.broken.push(i);
                }
            }
        }
        // panels with nothing under them fall
        if !report.broken.is_empty() {
            loop {
                let mut changed = false;
                for i in 0..self.panels.len() {
                    if self.panels[i].state != State::Standing || self.panels[i].row == 0 {
                        continue;
                    }
                    let (row, col) = (self.panels[i].row, self.panels[i].col);
                    let supported = self.panels.iter().any(|q| {
                        q.state == State::Standing && q.row + 1 == row && (q.col as isize - col as isize).abs() <= 1
                    });
                    if !supported {
                        let p = &mut self.panels[i];
                        p.state = State::Falling;
                        physics.world.bodies[p.body].set_body_type(RigidBodyType::Dynamic, true);
                        report.started_falling.push(i);
                        changed = true;
                    }
                }
                if !changed {
                    break;
                }
            }
        }
        report
    }

    /// Replaces panel `i` with chunks thrown along `dir`.
    fn shatter(&mut self, physics: &mut Physics, i: usize, dir: Vec3) -> Vec<Chunk> {
        let p = &mut self.panels[i];
        p.state = State::Broken;
        physics.remove_body(p.body);
        let nx = ((p.half.x * 2.0 / p.material.chunk).round() as usize).max(1);
        let ny = ((p.half.y * 2.0 / p.material.chunk).round() as usize).max(1);
        let half = Vec3::new(p.half.x / nx as f32, p.half.y / ny as f32, p.half.z) * 0.95;
        let mut chunks = Vec::with_capacity(nx * ny);
        for ix in 0..nx {
            for iy in 0..ny {
                let offset = Vec3::new(
                    -p.half.x + (ix as f32 + 0.5) * 2.0 * p.half.x / nx as f32,
                    -p.half.y + (iy as f32 + 0.5) * 2.0 * p.half.y / ny as f32,
                    0.0,
                );
                let (body, _) = physics.add_box(p.center + offset, half, p.material.density);
                // pieces fly along the hit and spread out from the panel's middle
                let spread = offset.normalize_or_zero() * 1.5;
                physics.set_velocity(body, dir * 3.0 + spread);
                chunks.push(Chunk { body, half, material: p.material });
            }
        }
        chunks
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn throw_crate_at_wall(speed: f32) -> (Wall, Report, f32) {
        let mut p = Physics::new();
        p.add_ground(50.0);
        let mut wall = Wall::new(&mut p, Vec3::new(-1.5, 0.0, 3.0), 3, 2, (1.0, 1.0), 0.1, WOOD);
        let (crate_, _) = p.add_box(Vec3::new(0.0, 0.5, 1.0), Vec3::splat(0.25), 30.0 / 0.125);
        p.set_velocity(crate_, Vec3::new(0.0, 1.0, speed));
        let mut all = Report::default();
        for _ in 0..90 {
            p.step();
            let r = wall.update(&mut p);
            all.broken.extend(r.broken);
            all.started_falling.extend(r.started_falling);
            all.chunks.extend(r.chunks);
        }
        let energy = 0.5 * p.mass(crate_) * speed * speed;
        (wall, all, energy)
    }

    #[test]
    fn a_fast_crate_breaks_wood_and_a_slow_one_does_not() {
        let (wall, fast, e_fast) = throw_crate_at_wall(12.0);
        println!("30 kg crate at 12 m/s ({e_fast:.0} J): {} panel(s) broken, {} chunks, {} fell, {} of 6 standing",
                 fast.broken.len(), fast.chunks.len(), fast.started_falling.len(), wall.standing());
        assert!(!fast.broken.is_empty(), "a 2160 J hit should break a 900 J wood panel");
        assert!(!fast.chunks.is_empty());

        let (wall, slow, e_slow) = throw_crate_at_wall(4.0);
        println!("30 kg crate at 4 m/s ({e_slow:.0} J): {} panel(s) broken, {} of 6 standing", slow.broken.len(), wall.standing());
        assert!(slow.broken.is_empty(), "a 240 J hit should not break a 900 J panel");
    }

    #[test]
    fn a_panel_with_nothing_under_it_falls() {
        let (wall, report, _) = throw_crate_at_wall(12.0);
        // the crate hits the bottom middle panel; the one above it is still held by its diagonal neighbours,
        // so break one more under it to leave the top middle panel with nothing below
        let broke_bottom_middle = report.broken.iter().any(|&i| wall.panels[i].row == 0 && wall.panels[i].col == 1);
        assert!(broke_bottom_middle, "expected the bottom middle panel to break");

        let mut p = Physics::new();
        p.add_ground(50.0);
        let mut wall = Wall::new(&mut p, Vec3::ZERO, 1, 3, (1.0, 1.0), 0.1, WOOD);
        let (ball, _) = p.add_ball(Vec3::new(0.5, 0.5, -1.0), 0.2, 4000.0);
        p.set_velocity(ball, Vec3::new(0.0, 0.0, 20.0));
        let mut fell = 0;
        for _ in 0..60 {
            p.step();
            fell += wall.update(&mut p).started_falling.len();
        }
        println!("column of 3, bottom knocked out: {fell} panel(s) above started falling");
        assert_eq!(fell, 2, "both panels above the broken one should fall");
    }
}
