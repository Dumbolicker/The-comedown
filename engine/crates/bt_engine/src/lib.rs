//! Borrowed Time's engine: fixed-step Rapier physics, an active ragdoll, breakable walls and a wgpu renderer.
//! Original code (clean room): built from public documentation, physics and anthropometry tables, not from any game.

pub mod destruct;
pub mod physics;
pub mod ragdoll;
pub mod render;

pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}
