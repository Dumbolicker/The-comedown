//! A small forward renderer on wgpu: instanced boxes, balls and capsules lit by one sun with soft shadows, under a
//! gradient sky with distance fog. It renders off-screen (for screenshots, tests and the headless demo); a window or
//! a web canvas can present the same frames.

use std::collections::HashMap;

use bytemuck::{Pod, Zeroable};
use wgpu::util::DeviceExt;

use crate::physics::{Mat4, Quat, Vec3};

const COLOR_FORMAT: wgpu::TextureFormat = wgpu::TextureFormat::Rgba8UnormSrgb;
const DEPTH_FORMAT: wgpu::TextureFormat = wgpu::TextureFormat::Depth32Float;
const SHADOW_SIZE: u32 = 2048;
const SAMPLES: u32 = 4;

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Vertex {
    pos: [f32; 3],
    normal: [f32; 3],
}

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Instance {
    model: [[f32; 4]; 4],
    color: [f32; 4],
}

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Globals {
    view_proj: [[f32; 4]; 4],
    light_view_proj: [[f32; 4]; 4],
    inv_view_proj: [[f32; 4]; 4],
    sun_dir: [f32; 4],
    sun_color: [f32; 4],
    sky_top: [f32; 4],
    sky_horizon: [f32; 4],
    ground: [f32; 4],
    camera_pos: [f32; 4],
    fog: [f32; 4],
}

/// What to draw. Boxes and balls are unit meshes scaled by `scale` (a box's full size, a ball's diameter);
/// a capsule's mesh is built for its exact size and `scale` stays at one.
#[derive(Clone, Copy, Debug)]
pub enum Shape {
    Box,
    Ball,
    Capsule { half_height: f32, radius: f32 },
}

#[derive(Clone, Copy, Debug)]
pub struct DrawItem {
    pub shape: Shape,
    pub position: Vec3,
    pub rotation: Quat,
    pub scale: Vec3,
    /// Linear-space RGBA.
    pub color: [f32; 4],
}

#[derive(Clone, Copy, Debug)]
pub struct Camera {
    pub eye: Vec3,
    pub target: Vec3,
    /// Vertical field of view, radians.
    pub fov_y: f32,
}

#[derive(Clone, Copy, Debug)]
pub struct Lighting {
    /// Unit vector toward the sun.
    pub sun_dir: Vec3,
    pub sun_color: [f32; 3],
    pub sky_top: [f32; 3],
    pub sky_horizon: [f32; 3],
    pub ground: [f32; 3],
    pub fog_start: f32,
    pub fog_end: f32,
    /// Half the width of the square the shadow map covers, centred on the camera target.
    pub shadow_extent: f32,
}

impl Default for Lighting {
    fn default() -> Self {
        Self {
            sun_dir: Vec3::new(-0.45, 0.8, -0.35).normalize(),
            sun_color: [1.05, 0.98, 0.88],
            sky_top: [0.30, 0.50, 0.85],
            sky_horizon: [0.72, 0.82, 0.93],
            ground: [0.32, 0.30, 0.25],
            fog_start: 40.0,
            fog_end: 160.0,
            shadow_extent: 30.0,
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
enum MeshKey {
    Box,
    Ball,
    Capsule(u32, u32),
}

struct Mesh {
    vertices: wgpu::Buffer,
    indices: wgpu::Buffer,
    count: u32,
}

pub struct Renderer {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pub width: u32,
    pub height: u32,
    adapter_info: wgpu::AdapterInfo,
    color: wgpu::Texture,
    msaa: wgpu::TextureView,
    depth: wgpu::TextureView,
    shadow: wgpu::TextureView,
    globals: wgpu::Buffer,
    bind_group: wgpu::BindGroup,
    shadow_bind_group: wgpu::BindGroup,
    main_pipeline: wgpu::RenderPipeline,
    shadow_pipeline: wgpu::RenderPipeline,
    sky_pipeline: wgpu::RenderPipeline,
    meshes: HashMap<MeshKey, Mesh>,
    instances: wgpu::Buffer,
    instance_capacity: u64,
    readback: wgpu::Buffer,
    padded_row: u32,
    pub lighting: Lighting,
}

impl Renderer {
    /// A renderer with no window. Picks any adapter, including a software one (Mesa's lavapipe) on machines without
    /// a graphics card.
    pub fn new_headless(width: u32, height: u32) -> Result<Self, String> {
        pollster::block_on(Self::new_async(width, height))
    }

    async fn new_async(width: u32, height: u32) -> Result<Self, String> {
        let mut desc = wgpu::InstanceDescriptor::new_without_display_handle_from_env();
        desc.backends = wgpu::Backends::VULKAN | wgpu::Backends::GL | wgpu::Backends::METAL | wgpu::Backends::DX12;
        let instance = wgpu::Instance::new(desc);
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, ..Default::default() })
            .await
            .map_err(|e| format!("no graphics adapter: {e}"))?;
        let adapter_info = adapter.get_info();
        let (device, queue) = adapter
            .request_device(&wgpu::DeviceDescriptor { label: Some("bt device"), required_limits: wgpu::Limits::downlevel_defaults().using_resolution(adapter.limits()), ..Default::default() })
            .await
            .map_err(|e| format!("device: {e}"))?;

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor { label: Some("bt shader"), source: wgpu::ShaderSource::Wgsl(include_str!("shader.wgsl").into()) });

        let texture = |label: &str, w: u32, h: u32, format: wgpu::TextureFormat, samples: u32, usage: wgpu::TextureUsages| {
            device.create_texture(&wgpu::TextureDescriptor {
                label: Some(label),
                size: wgpu::Extent3d { width: w, height: h, depth_or_array_layers: 1 },
                mip_level_count: 1,
                sample_count: samples,
                dimension: wgpu::TextureDimension::D2,
                format,
                usage,
                view_formats: &[],
            })
        };
        let color = texture("color", width, height, COLOR_FORMAT, 1, wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC);
        let msaa = texture("msaa", width, height, COLOR_FORMAT, SAMPLES, wgpu::TextureUsages::RENDER_ATTACHMENT).create_view(&Default::default());
        let depth = texture("depth", width, height, DEPTH_FORMAT, SAMPLES, wgpu::TextureUsages::RENDER_ATTACHMENT).create_view(&Default::default());
        let shadow = texture("shadow", SHADOW_SIZE, SHADOW_SIZE, DEPTH_FORMAT, 1, wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::TEXTURE_BINDING)
            .create_view(&Default::default());

        let globals = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("globals"),
            size: std::mem::size_of::<Globals>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });
        let shadow_sampler = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("shadow sampler"),
            mag_filter: wgpu::FilterMode::Linear,
            min_filter: wgpu::FilterMode::Linear,
            compare: Some(wgpu::CompareFunction::LessEqual),
            ..Default::default()
        });
        let layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("globals layout"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::VERTEX_FRAGMENT,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false, min_binding_size: None },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture { sample_type: wgpu::TextureSampleType::Depth, view_dimension: wgpu::TextureViewDimension::D2, multisampled: false },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry { binding: 2, visibility: wgpu::ShaderStages::FRAGMENT, ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::Comparison), count: None },
            ],
        });
        // The shadow pass draws into the shadow map, so it can't also sample it: it gets a layout without bindings 1 and 2.
        let shadow_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("shadow layout"),
            entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: wgpu::ShaderStages::VERTEX_FRAGMENT,
                ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false, min_binding_size: None },
                count: None,
            }],
        });
        let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("globals"),
            layout: &layout,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: globals.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: wgpu::BindingResource::TextureView(&shadow) },
                wgpu::BindGroupEntry { binding: 2, resource: wgpu::BindingResource::Sampler(&shadow_sampler) },
            ],
        });
        let shadow_bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("shadow globals"),
            layout: &shadow_layout,
            entries: &[wgpu::BindGroupEntry { binding: 0, resource: globals.as_entire_binding() }],
        });
        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor { label: Some("main"), bind_group_layouts: &[Some(&layout)], immediate_size: 0 });
        let shadow_pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor { label: Some("shadow"), bind_group_layouts: &[Some(&shadow_layout)], immediate_size: 0 });

        let vertex_layouts = [
            Some(wgpu::VertexBufferLayout {
                array_stride: std::mem::size_of::<Vertex>() as u64,
                step_mode: wgpu::VertexStepMode::Vertex,
                attributes: &wgpu::vertex_attr_array![0 => Float32x3, 1 => Float32x3],
            }),
            Some(wgpu::VertexBufferLayout {
                array_stride: std::mem::size_of::<Instance>() as u64,
                step_mode: wgpu::VertexStepMode::Instance,
                attributes: &wgpu::vertex_attr_array![2 => Float32x4, 3 => Float32x4, 4 => Float32x4, 5 => Float32x4, 6 => Float32x4],
            }),
        ];
        let depth_state = |write: bool, compare: wgpu::CompareFunction, bias: wgpu::DepthBiasState| wgpu::DepthStencilState {
            format: DEPTH_FORMAT,
            depth_write_enabled: Some(write),
            depth_compare: Some(compare),
            stencil: Default::default(),
            bias,
        };
        let main_pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("main"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState { module: &shader, entry_point: Some("vs_main"), compilation_options: Default::default(), buffers: &vertex_layouts },
            primitive: wgpu::PrimitiveState { cull_mode: Some(wgpu::Face::Back), ..Default::default() },
            depth_stencil: Some(depth_state(true, wgpu::CompareFunction::Less, Default::default())),
            multisample: wgpu::MultisampleState { count: SAMPLES, ..Default::default() },
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_main"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState { format: COLOR_FORMAT, blend: None, write_mask: wgpu::ColorWrites::ALL })],
            }),
            multiview_mask: None,
            cache: None,
        });
        let shadow_pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("shadow"),
            layout: Some(&shadow_pipeline_layout),
            vertex: wgpu::VertexState { module: &shader, entry_point: Some("vs_shadow"), compilation_options: Default::default(), buffers: &vertex_layouts },
            primitive: wgpu::PrimitiveState { cull_mode: None, ..Default::default() },
            depth_stencil: Some(depth_state(true, wgpu::CompareFunction::Less, wgpu::DepthBiasState { constant: 2, slope_scale: 2.0, clamp: 0.0 })),
            multisample: Default::default(),
            fragment: None,
            multiview_mask: None,
            cache: None,
        });
        let sky_pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("sky"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState { module: &shader, entry_point: Some("vs_sky"), compilation_options: Default::default(), buffers: &[] },
            primitive: Default::default(),
            depth_stencil: Some(depth_state(false, wgpu::CompareFunction::Always, Default::default())),
            multisample: wgpu::MultisampleState { count: SAMPLES, ..Default::default() },
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_sky"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState { format: COLOR_FORMAT, blend: None, write_mask: wgpu::ColorWrites::ALL })],
            }),
            multiview_mask: None,
            cache: None,
        });

        let padded_row = (width * 4).div_ceil(wgpu::COPY_BYTES_PER_ROW_ALIGNMENT) * wgpu::COPY_BYTES_PER_ROW_ALIGNMENT;
        let readback = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("readback"),
            size: (padded_row * height) as u64,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });
        let instance_capacity = 1024;
        let instances = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("instances"),
            size: instance_capacity * std::mem::size_of::<Instance>() as u64,
            usage: wgpu::BufferUsages::VERTEX | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        let mut r = Self {
            device,
            queue,
            width,
            height,
            adapter_info,
            color,
            msaa,
            depth,
            shadow,
            globals,
            bind_group,
            shadow_bind_group,
            main_pipeline,
            shadow_pipeline,
            sky_pipeline,
            meshes: HashMap::new(),
            instances,
            instance_capacity,
            readback,
            padded_row,
            lighting: Lighting::default(),
        };
        r.add_mesh(MeshKey::Box, cube());
        r.add_mesh(MeshKey::Ball, sphere(0.5, 24, 16));
        Ok(r)
    }

    /// The graphics adapter in use, such as "llvmpipe (Vulkan)".
    pub fn adapter(&self) -> String {
        format!("{} ({:?})", self.adapter_info.name, self.adapter_info.backend)
    }

    fn add_mesh(&mut self, key: MeshKey, (vertices, indices): (Vec<Vertex>, Vec<u32>)) {
        let v = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor { label: Some("vertices"), contents: bytemuck::cast_slice(&vertices), usage: wgpu::BufferUsages::VERTEX });
        let i = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor { label: Some("indices"), contents: bytemuck::cast_slice(&indices), usage: wgpu::BufferUsages::INDEX });
        self.meshes.insert(key, Mesh { vertices: v, indices: i, count: indices.len() as u32 });
    }

    /// Draws one frame and returns it as an sRGB image.
    pub fn render(&mut self, camera: &Camera, items: &[DrawItem]) -> image::RgbaImage {
        // group instances by mesh
        let mut groups: HashMap<MeshKey, Vec<Instance>> = HashMap::new();
        for it in items {
            let key = match it.shape {
                Shape::Box => MeshKey::Box,
                Shape::Ball => MeshKey::Ball,
                Shape::Capsule { half_height, radius } => {
                    let key = MeshKey::Capsule((half_height * 1000.0).round() as u32, (radius * 1000.0).round() as u32);
                    if !self.meshes.contains_key(&key) {
                        self.add_mesh(key, capsule(half_height, radius, 20, 8));
                    }
                    key
                }
            };
            let model = Mat4::from_scale_rotation_translation(it.scale, it.rotation, it.position);
            groups.entry(key).or_default().push(Instance { model: model.to_cols_array_2d(), color: it.color });
        }
        let mut order: Vec<(MeshKey, u64, u32)> = Vec::new();
        let mut all: Vec<Instance> = Vec::with_capacity(items.len());
        for (key, list) in &groups {
            order.push((*key, all.len() as u64, list.len() as u32));
            all.extend_from_slice(list);
        }
        if all.len() as u64 > self.instance_capacity {
            self.instance_capacity = (all.len() as u64).next_power_of_two();
            self.instances = self.device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("instances"),
                size: self.instance_capacity * std::mem::size_of::<Instance>() as u64,
                usage: wgpu::BufferUsages::VERTEX | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            });
        }
        if !all.is_empty() {
            self.queue.write_buffer(&self.instances, 0, bytemuck::cast_slice(&all));
        }

        // camera and sun (glam's older matrix helpers, which match wgpu's 0..1 depth range)
        #[allow(deprecated)]
        let (view, proj, light_view, light_proj) = {
            let aspect = self.width as f32 / self.height as f32;
            let l = &self.lighting;
            let e = l.shadow_extent;
            (
                Mat4::look_at_rh(camera.eye, camera.target, Vec3::Y),
                Mat4::perspective_rh(camera.fov_y, aspect, 0.1, 400.0),
                Mat4::look_at_rh(camera.target + l.sun_dir * 80.0, camera.target, Vec3::Y),
                Mat4::orthographic_rh(-e, e, -e, e, 1.0, 200.0),
            )
        };
        let view_proj = proj * view;
        let l = &self.lighting;
        let g = Globals {
            view_proj: view_proj.to_cols_array_2d(),
            light_view_proj: (light_proj * light_view).to_cols_array_2d(),
            inv_view_proj: view_proj.inverse().to_cols_array_2d(),
            sun_dir: [l.sun_dir.x, l.sun_dir.y, l.sun_dir.z, 0.0],
            sun_color: [l.sun_color[0], l.sun_color[1], l.sun_color[2], 1.0],
            sky_top: [l.sky_top[0], l.sky_top[1], l.sky_top[2], 1.0],
            sky_horizon: [l.sky_horizon[0], l.sky_horizon[1], l.sky_horizon[2], 1.0],
            ground: [l.ground[0], l.ground[1], l.ground[2], 1.0],
            camera_pos: [camera.eye.x, camera.eye.y, camera.eye.z, 1.0],
            fog: [l.fog_start, l.fog_end, 1.0 / SHADOW_SIZE as f32, 0.0],
        };
        self.queue.write_buffer(&self.globals, 0, bytemuck::bytes_of(&g));

        let mut encoder = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: Some("frame") });
        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("shadow"),
                color_attachments: &[],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &self.shadow,
                    depth_ops: Some(wgpu::Operations { load: wgpu::LoadOp::Clear(1.0), store: wgpu::StoreOp::Store }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            pass.set_pipeline(&self.shadow_pipeline);
            pass.set_bind_group(0, &self.shadow_bind_group, &[]);
            self.draw_groups(&mut pass, &order);
        }
        let color_view = self.color.create_view(&Default::default());
        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("main"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &self.msaa,
                    depth_slice: None,
                    resolve_target: Some(&color_view),
                    ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Discard },
                })],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &self.depth,
                    depth_ops: Some(wgpu::Operations { load: wgpu::LoadOp::Clear(1.0), store: wgpu::StoreOp::Discard }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            pass.set_bind_group(0, &self.bind_group, &[]);
            pass.set_pipeline(&self.sky_pipeline);
            pass.draw(0..3, 0..1);
            pass.set_pipeline(&self.main_pipeline);
            self.draw_groups(&mut pass, &order);
        }
        encoder.copy_texture_to_buffer(
            wgpu::TexelCopyTextureInfo { texture: &self.color, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            wgpu::TexelCopyBufferInfo {
                buffer: &self.readback,
                layout: wgpu::TexelCopyBufferLayout { offset: 0, bytes_per_row: Some(self.padded_row), rows_per_image: Some(self.height) },
            },
            wgpu::Extent3d { width: self.width, height: self.height, depth_or_array_layers: 1 },
        );
        self.queue.submit(Some(encoder.finish()));

        let slice = self.readback.slice(..);
        slice.map_async(wgpu::MapMode::Read, |_| {});
        let _ = self.device.poll(wgpu::PollType::wait_indefinitely());
        let mut img = image::RgbaImage::new(self.width, self.height);
        {
            let data = slice.get_mapped_range().expect("the readback buffer maps after the frame finishes");
            for y in 0..self.height as usize {
                let row = &data[y * self.padded_row as usize..y * self.padded_row as usize + self.width as usize * 4];
                img.as_mut()[y * self.width as usize * 4..(y + 1) * self.width as usize * 4].copy_from_slice(row);
            }
        }
        self.readback.unmap();
        img
    }

    fn draw_groups(&self, pass: &mut wgpu::RenderPass<'_>, order: &[(MeshKey, u64, u32)]) {
        let stride = std::mem::size_of::<Instance>() as u64;
        for &(key, first, count) in order {
            let mesh = &self.meshes[&key];
            pass.set_vertex_buffer(0, mesh.vertices.slice(..));
            pass.set_vertex_buffer(1, self.instances.slice(first * stride..(first + count as u64) * stride));
            pass.set_index_buffer(mesh.indices.slice(..), wgpu::IndexFormat::Uint32);
            pass.draw_indexed(0..mesh.count, 0, 0..count);
        }
    }
}

/// A unit cube centred on the origin, flat-shaded.
fn cube() -> (Vec<Vertex>, Vec<u32>) {
    let faces: [([f32; 3], [f32; 3], [f32; 3]); 6] = [
        ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]),
        ([-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]),
        ([0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]),
        ([0.0, -1.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]),
        ([0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
        ([0.0, 0.0, -1.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
    ];
    let mut v = Vec::with_capacity(24);
    let mut i = Vec::with_capacity(36);
    for (n, a, b) in faces {
        let (n, a, b) = (Vec3::from(n), Vec3::from(a), Vec3::from(b));
        let base = v.len() as u32;
        for (sa, sb) in [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)] {
            let p = n * 0.5 + a * 0.5 * sa + b * 0.5 * sb;
            v.push(Vertex { pos: p.into(), normal: n.into() });
        }
        // counter-clockwise when seen from outside: a × b must point along n
        if a.cross(b).dot(n) > 0.0 {
            i.extend_from_slice(&[base, base + 1, base + 2, base, base + 2, base + 3]);
        } else {
            i.extend_from_slice(&[base, base + 2, base + 1, base, base + 3, base + 2]);
        }
    }
    (v, i)
}

/// A UV sphere.
fn sphere(radius: f32, segments: u32, rings: u32) -> (Vec<Vertex>, Vec<u32>) {
    let mut v = Vec::new();
    let mut idx = Vec::new();
    for r in 0..=rings {
        let phi = std::f32::consts::PI * r as f32 / rings as f32;
        for s in 0..=segments {
            let theta = std::f32::consts::TAU * s as f32 / segments as f32;
            let n = Vec3::new(phi.sin() * theta.cos(), phi.cos(), phi.sin() * theta.sin());
            v.push(Vertex { pos: (n * radius).into(), normal: n.into() });
        }
    }
    let w = segments + 1;
    for r in 0..rings {
        for s in 0..segments {
            let (a, b, c, d) = (r * w + s, (r + 1) * w + s, (r + 1) * w + s + 1, r * w + s + 1);
            idx.extend_from_slice(&[a, d, b, b, d, c]);
        }
    }
    (v, idx)
}

/// A capsule along Y: two half-spheres joined by a cylinder.
fn capsule(half_height: f32, radius: f32, segments: u32, cap_rings: u32) -> (Vec<Vertex>, Vec<u32>) {
    let mut v = Vec::new();
    let mut idx = Vec::new();
    let rings = cap_rings * 2 + 1;
    for r in 0..=rings {
        // top cap rings 0..=cap_rings, bottom cap rings cap_rings+1..=rings
        let (phi, y_off) = if r <= cap_rings {
            (std::f32::consts::FRAC_PI_2 * r as f32 / cap_rings as f32, half_height)
        } else {
            (std::f32::consts::FRAC_PI_2 * (1.0 + (r - cap_rings - 1) as f32 / cap_rings as f32), -half_height)
        };
        for s in 0..=segments {
            let theta = std::f32::consts::TAU * s as f32 / segments as f32;
            let n = Vec3::new(phi.sin() * theta.cos(), phi.cos(), phi.sin() * theta.sin());
            v.push(Vertex { pos: (n * radius + Vec3::new(0.0, y_off, 0.0)).into(), normal: n.into() });
        }
    }
    let w = segments + 1;
    for r in 0..rings {
        for s in 0..segments {
            let (a, b, c, d) = (r * w + s, (r + 1) * w + s, (r + 1) * w + s + 1, r * w + s + 1);
            idx.extend_from_slice(&[a, d, b, b, d, c]);
        }
    }
    (v, idx)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Every triangle winds counter-clockwise seen from outside (front faces), or back-face culling would hide it.
    fn faces_point_outward(name: &str, (v, i): (Vec<Vertex>, Vec<u32>)) {
        let mut bad = 0;
        let mut total = 0;
        for tri in i.chunks(3) {
            let (a, b, c) = (Vec3::from(v[tri[0] as usize].pos), Vec3::from(v[tri[1] as usize].pos), Vec3::from(v[tri[2] as usize].pos));
            let area = (b - a).cross(c - a);
            if area.length() < 1e-6 {
                continue; // degenerate triangles at the poles
            }
            let n = Vec3::from(v[tri[0] as usize].normal) + Vec3::from(v[tri[1] as usize].normal) + Vec3::from(v[tri[2] as usize].normal);
            total += 1;
            if area.dot(n) <= 0.0 {
                bad += 1;
            }
        }
        assert_eq!(bad, 0, "{name}: {bad} of {total} triangles wind inward");
    }

    #[test]
    fn meshes_face_outward() {
        faces_point_outward("cube", cube());
        faces_point_outward("sphere", sphere(0.5, 24, 16));
        faces_point_outward("capsule", capsule(0.2, 0.1, 20, 8));
    }
}
