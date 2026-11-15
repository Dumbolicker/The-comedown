//! Platform services the web game calls through Tauri commands (see `window.BT_PLATFORM` in dist/index.html):
//! achievements and a saved profile (records, unlocks, settings live in the profile JSON).
//!
//! * Default build: achievements are ignored and the profile is a file in the app's data folder.
//! * `--features steam`: achievements go to Steamworks and the profile is also written to Steam Cloud
//!   (Remote Storage), so it follows the player between computers. The App ID comes from `BT_STEAM_APPID`
//!   at runtime and falls back to 480, Valve's public test app, for development.
use std::{fs, path::PathBuf};
use tauri::{Builder, Manager, Runtime};

const PROFILE_FILE: &str = "profile.json";

/// Feat names from the game ("Frequent Flyer") become Steam API names ("FEAT_FREQUENT_FLYER").
#[cfg_attr(not(feature = "steam"), allow(dead_code))]
pub fn api_name(feat: &str) -> String {
    let mut out = String::from("FEAT_");
    let mut last_us = true;
    for c in feat.chars() {
        if c.is_ascii_alphanumeric() {
            out.push(c.to_ascii_uppercase());
            last_us = false;
        } else if !last_us {
            out.push('_');
            last_us = true;
        }
    }
    while out.ends_with('_') {
        out.pop();
    }
    out
}

fn profile_path<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    let dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join(PROFILE_FILE))
}

#[tauri::command]
fn platform_name() -> &'static str {
    if cfg!(feature = "steam") { "steam" } else { "desktop" }
}

#[tauri::command]
fn unlock_achievement(feat: String) -> Result<(), String> {
    #[cfg(feature = "steam")]
    {
        return steam::unlock(&api_name(&feat));
    }
    #[cfg(not(feature = "steam"))]
    {
        let _ = feat;
        Ok(())
    }
}

#[tauri::command]
fn save_profile<R: Runtime>(app: tauri::AppHandle<R>, json: String) -> Result<(), String> {
    if json.len() > 256 * 1024 {
        return Err("profile too large".into());
    }
    serde_check(&json)?;
    let path = profile_path(&app)?;
    let tmp = path.with_extension("json.tmp");
    fs::write(&tmp, json.as_bytes()).map_err(|e| e.to_string())?;
    fs::rename(&tmp, &path).map_err(|e| e.to_string())?; // atomic replace: a crash never leaves half a file
    #[cfg(feature = "steam")]
    steam::cloud_write(PROFILE_FILE, json.as_bytes())?;
    Ok(())
}

#[tauri::command]
fn load_profile<R: Runtime>(app: tauri::AppHandle<R>) -> Result<Option<String>, String> {
    #[cfg(feature = "steam")]
    if let Some(s) = steam::cloud_read(PROFILE_FILE) {
        return Ok(Some(s));
    }
    let path = profile_path(&app)?;
    Ok(fs::read_to_string(path).ok())
}

/// Cheap shape check so a broken page can't write garbage: the profile must be a JSON object.
fn serde_check(json: &str) -> Result<(), String> {
    let t = json.trim();
    if t.starts_with('{') && t.ends_with('}') { Ok(()) } else { Err("profile must be a JSON object".into()) }
}

pub fn register<R: Runtime>(builder: Builder<R>) -> Builder<R> {
    #[cfg(feature = "steam")]
    steam::init();
    builder.invoke_handler(tauri::generate_handler![platform_name, unlock_achievement, save_profile, load_profile])
}

#[cfg(feature = "steam")]
mod steam {
    use std::io::{Read, Write};
    use std::sync::OnceLock;
    use steamworks::Client;

    static CLIENT: OnceLock<Option<Client>> = OnceLock::new();

    pub fn init() {
        let app_id: u32 = std::env::var("BT_STEAM_APPID").ok().and_then(|v| v.parse().ok()).unwrap_or(480);
        let client = match Client::init_app(app_id) {
            Ok(c) => Some(c),
            Err(e) => {
                eprintln!("Steam not available ({e}); achievements and cloud saves are off");
                None
            }
        };
        if let Some(c) = client.clone() {
            // Steam callbacks must be pumped regularly
            std::thread::spawn(move || loop {
                c.run_callbacks();
                std::thread::sleep(std::time::Duration::from_millis(100));
            });
        }
        let _ = CLIENT.set(client);
    }

    fn client() -> Option<&'static Client> {
        CLIENT.get().and_then(|c| c.as_ref())
    }

    pub fn unlock(api: &str) -> Result<(), String> {
        let Some(c) = client() else { return Ok(()) };
        let stats = c.user_stats();
        stats.achievement(api).set().map_err(|_| format!("unknown achievement {api}"))?;
        stats.store_stats().map_err(|_| "could not store stats".to_string())
    }

    pub fn cloud_write(name: &str, data: &[u8]) -> Result<(), String> {
        let Some(c) = client() else { return Ok(()) };
        let rs = c.remote_storage();
        if !rs.is_cloud_enabled_for_account() || !rs.is_cloud_enabled_for_app() {
            return Ok(());
        }
        let mut w = rs.file(name).write();
        w.write_all(data).map_err(|e| e.to_string())
    }

    pub fn cloud_read(name: &str) -> Option<String> {
        let c = client()?;
        let f = c.remote_storage().file(name);
        if !f.exists() {
            return None;
        }
        let mut s = String::new();
        f.read().read_to_string(&mut s).ok()?;
        Some(s)
    }
}

#[cfg(test)]
mod tests {
    use super::api_name;
    #[test]
    fn feat_names_map_to_stable_api_names() {
        assert_eq!(api_name("Frequent Flyer"), "FEAT_FREQUENT_FLYER");
        assert_eq!(api_name("Against All Odds"), "FEAT_AGAINST_ALL_ODDS");
        assert_eq!(api_name("Water Damage!"), "FEAT_WATER_DAMAGE");
    }
}
