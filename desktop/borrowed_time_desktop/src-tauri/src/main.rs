// Desktop shell for Borrowed Time. The game itself is ../dist/index.html (WebGL), bundled into the exe.
// Hides the console window on Windows release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("Borrowed Time failed to start");
}
