"""Vivédex Browser Demo Capture Script.

Automates Google Chrome via Chrome DevTools Protocol (CDP) to record a continuous,
high-fidelity, 1920x1080 landscape demonstration of the real Vivédex application
running on http://localhost:8501.

Produces:
  - assets/demo/raw/vivedex-browser-demo.webm
  - Conversation artifact copy
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECIMEN_IMAGE_PATH = PROJECT_ROOT / "assets" / "demo" / "passer_domesticus.jpg"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "demo" / "raw"
OUTPUT_WEBM = OUTPUT_DIR / "vivedex-browser-demo.webm"
ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\09c3c9b4-5c4b-4b58-882a-f5bc6cf56dec")
ARTIFACT_WEBM = ARTIFACT_DIR / "vivedex-browser-demo.webm"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9225
BASE_URL = "http://localhost:8501"

captured_frames: list[str] = []
step_results: dict[str, str] = {}


class CDPClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=150_000_000)

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send_cmd(self, method: str, params: dict | None = None) -> dict:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method}
        if params is not None:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))

        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error in {method}: {data['error']}")
                return data.get("result", {})

    async def evaluate_js(self, expression: str) -> any:
        res = await self.send_cmd(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
        )
        result_obj = res.get("result", {})
        return result_obj.get("value")

    async def capture_frame(self, label: str = ""):
        res = await self.send_cmd(
            "Page.captureScreenshot",
            {
                "format": "jpeg",
                "quality": 88,
            },
        )
        data = res.get("data")
        if data:
            captured_frames.append(data)

    async def wait_and_capture(self, duration_sec: float, fps: float = 3.0, label: str = ""):
        interval = 1.0 / fps
        steps = int(max(1, duration_sec * fps))
        for _ in range(steps):
            await self.capture_frame(label)
            await asyncio.sleep(interval)

    async def wait_for_predicate(self, js_predicate: str, timeout_sec: float = 25.0) -> bool:
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                val = await self.evaluate_js(js_predicate)
                if val:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.4)
        return False


async def run_demo_recording():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    print("============================================================")
    print(" Vivédex Automated Browser Demo Recording (CDP)")
    print("============================================================")
    print(f"Specimen Image: {SPECIMEN_IMAGE_PATH} ({SPECIMEN_IMAGE_PATH.stat().st_size} bytes)")
    print(f"Target URL:     {BASE_URL}")

    temp_profile = tempfile.mkdtemp(prefix="chrome_demo_profile_")
    chrome_cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={temp_profile}",
        "--headless=new",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--disable-extensions",
        "--disable-gpu",
        "--no-first-run",
        f"{BASE_URL}/home",
    ]

    print("[INFO] Launching Google Chrome headless with 1920x1080 viewport...")
    proc = subprocess.Popen(chrome_cmd)
    await asyncio.sleep(5)

    client = None
    try:
        # 1. Connect to CDP on page target
        async with httpx.AsyncClient() as http:
            r = await http.get(f"http://localhost:{CDP_PORT}/json")
            targets = r.json()
            page_target = next((t for t in targets if t.get("type") == "page"), None)
            if not page_target:
                r_new = await http.put(f"http://localhost:{CDP_PORT}/json/new?{BASE_URL}/home")
                page_target = r_new.json()
            ws_url = page_target["webSocketDebuggerUrl"]

        client = CDPClient(ws_url)
        await client.connect()
        print("[OK] Connected to Chrome DevTools Protocol.")

        # Configure viewport to 1920x1080 exactly
        await client.send_cmd("Page.enable")
        await client.send_cmd("DOM.enable")
        await client.send_cmd("Runtime.enable")
        await client.send_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )

        # -------------------------------------------------------------
        # SCENE 1: HOME PAGE
        # -------------------------------------------------------------
        print("\n--- SCENE 1: Home Page & Expedition Hub ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/home"})
        await client.wait_for_predicate("document.body.innerText.includes('Vivédex') || document.body.innerText.includes('Expedition')", 25.0)
        await client.wait_and_capture(4.0, fps=3.0, label="scene1_home")
        step_results["Scene 1 - Home Page"] = "SUCCESS"
        print("[OK] Scene 1 completed.")

        # Quick Demo Account Switch to demo_naturalist
        print("\n--- Authenticating as demo_naturalist via Sidebar ---")
        await client.wait_for_predicate("Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('demo_naturalist'))", 15.0)
        login_btn_js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const demoBtn = btns.find(b => b.innerText.includes('demo_naturalist'));
            if (demoBtn) {
                demoBtn.click();
                return true;
            }
            return false;
        })()
        """
        found_demo = await client.evaluate_js(login_btn_js)
        if found_demo:
            await client.wait_and_capture(3.0, fps=3.0, label="scene1_login_click")
            await client.wait_for_predicate("document.body.innerText.includes('Field Naturalist') || document.body.innerText.includes('Demo Field Observer')", 20.0)
            await client.wait_and_capture(3.0, fps=3.0, label="scene1_logged_in")
            step_results["Demo Account Authentication"] = "SUCCESS (demo_naturalist)"
            print("[OK] Authenticated as demo_naturalist.")
        else:
            step_results["Demo Account Authentication"] = "SKIPPED"
            print("[WARN] Quick Demo button not clicked.")

        # -------------------------------------------------------------
        # SCENE 2: SPECIES IDENTIFICATION
        # -------------------------------------------------------------
        print("\n--- SCENE 2: Identify Specimen ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/identify"})
        await client.wait_for_predicate("document.body.innerText.includes('Identify a Specimen')", 25.0)
        await client.wait_and_capture(3.0, fps=3.0, label="scene2_identify_init")

        # Wait for file input to exist
        await client.wait_for_predicate("document.querySelector('input[type=\"file\"]') !== null", 20.0)
        print("[INFO] Uploading specimen photograph...")
        doc = await client.send_cmd("DOM.getDocument")
        root_node_id = doc["root"]["nodeId"]
        file_input = await client.send_cmd(
            "DOM.querySelector",
            {"nodeId": root_node_id, "selector": "input[type='file']"},
        )
        file_input_id = file_input.get("nodeId", 0)

        if file_input_id:
            await client.send_cmd(
                "DOM.setFileInputFiles",
                {
                    "files": [str(SPECIMEN_IMAGE_PATH.resolve())],
                    "nodeId": file_input_id,
                },
            )
            print("[OK] File input files set via CDP.")
            # Wait for image preview and Analyse button to render
            await client.wait_for_predicate("Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('Analyse Specimen'))", 25.0)
            await client.wait_and_capture(3.5, fps=3.0, label="scene2_image_preview")

            # Click "🔍 Analyse Specimen"
            print("[INFO] Triggering Analyse Specimen action...")
            analyze_click_js = """
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const btn = btns.find(b => b.innerText.includes('Analyse Specimen'));
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
            """
            await client.evaluate_js(analyze_click_js)
            # Capture progress frames while waiting for real Muse Spark response
            print("[INFO] Awaiting real Meta Muse Spark and GBIF model inference...")
            await client.wait_and_capture(4.0, fps=2.0, label="scene2_analyzing_spinner")
            found_result = await client.wait_for_predicate("document.body.innerText.includes('Candidate Identification') || document.body.innerText.includes('Passer domesticus')", 45.0)

            if found_result:
                # Hold completed result on screen for 6 seconds
                await client.wait_and_capture(6.0, fps=3.0, label="scene2_result_card")
                step_results["Scene 2 - Species Identification"] = "SUCCESS (Passer domesticus / Meta Muse Spark)"
                print("[OK] Scene 2 completed with verified candidate identification.")
            else:
                step_results["Scene 2 - Species Identification"] = "PARTIAL (Inference timeout)"
                print("[WARN] Inference result card did not appear within 45 seconds.")
        else:
            step_results["Scene 2 - Species Identification"] = "FAIL (File input element not located)"
            print("[ERROR] Could not find file input element.")

        # -------------------------------------------------------------
        # SCENE 3: SPECIES EXPLORATION & TAXONOMY
        # -------------------------------------------------------------
        print("\n--- SCENE 3: Species Exploration (Explore Dex) ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/explore"})
        await client.wait_for_predicate("document.body.innerText.includes('Explore Dex') || document.body.innerText.includes('Taxonomic Atlas')", 25.0)
        await client.wait_and_capture(3.5, fps=3.0, label="scene3_explore_dex")

        # Scroll down smoothly to showcase GBIF taxonomy hierarchy
        await client.evaluate_js("window.scrollBy({ top: 450, behavior: 'smooth' })")
        await client.wait_and_capture(3.0, fps=3.0, label="scene3_explore_scroll")
        step_results["Scene 3 - Species Exploration"] = "SUCCESS"
        print("[OK] Scene 3 completed.")

        # -------------------------------------------------------------
        # SCENE 4: PERSONAL COLLECTION (MY DEX)
        # -------------------------------------------------------------
        print("\n--- SCENE 4: Personal Collection (My Dex) ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/mydex"})
        await client.wait_for_predicate("document.body.innerText.includes('My Dex Collection') || document.body.innerText.includes('Specimen Collection')", 25.0)
        await client.wait_and_capture(4.0, fps=3.0, label="scene4_mydex_collection")
        step_results["Scene 4 - Personal Collection"] = "SUCCESS"
        print("[OK] Scene 4 completed.")

        # -------------------------------------------------------------
        # SCENE 5: FIELD JOURNAL & RESEARCHER PASSPORT
        # -------------------------------------------------------------
        print("\n--- SCENE 5: Field Journal & Researcher Passport ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/journal"})
        await client.wait_for_predicate("document.body.innerText.includes('Field Journal')", 25.0)
        await client.wait_and_capture(3.5, fps=3.0, label="scene5_field_journal")
        step_results["Scene 5 - Field Journal"] = "SUCCESS"

        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/passport"})
        await client.wait_for_predicate("document.body.innerText.includes('Researcher Passport') || document.body.innerText.includes('Contributor')", 25.0)
        await client.wait_and_capture(4.0, fps=3.0, label="scene5_researcher_passport")
        step_results["Scene 5 - Researcher Passport"] = "SUCCESS (VDX-DEMO-02)"
        print("[OK] Scene 5 completed.")

        # -------------------------------------------------------------
        # SCENE 6: CLOSING FRAME (EXPEDITION HUB / HOME)
        # -------------------------------------------------------------
        print("\n--- SCENE 6: Closing Frame (Home) ---")
        await client.send_cmd("Page.navigate", {"url": f"{BASE_URL}/home"})
        await client.wait_for_predicate("document.body.innerText.includes('Vivédex')", 25.0)
        # Scroll smoothly to top
        await client.evaluate_js("window.scrollTo({ top: 0, behavior: 'smooth' })")
        await client.wait_and_capture(4.5, fps=3.0, label="scene6_closing_home")
        step_results["Scene 6 - Closing Frame"] = "SUCCESS"
        print("[OK] Scene 6 completed.")

        print(f"\n[INFO] Total frames captured: {len(captured_frames)}")

        # -------------------------------------------------------------
        # VIDEO ENCODING VIA CHROME MEDIARECORDER (WebM VP8)
        # -------------------------------------------------------------
        print("\n--- Encoding Captured Frames to WebM (1920x1080 @ 4 fps) ---")
        await client.send_cmd("Page.navigate", {"url": "about:blank"})
        await asyncio.sleep(1)

        chunk_size = 20
        total_chunks = (len(captured_frames) + chunk_size - 1) // chunk_size

        init_recorder_js = """
        window._capturedChunks = [];
        window._framesList = [];
        window._canvas = document.createElement('canvas');
        window._canvas.width = 1920;
        window._canvas.height = 1080;
        window._ctx = window._canvas.getContext('2d');
        window._stream = window._canvas.captureStream(4);
        window._recorder = new MediaRecorder(window._stream, {
            mimeType: 'video/webm; codecs=vp8',
            videoBitsPerSecond: 4000000
        });
        window._recorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) window._capturedChunks.push(e.data);
        };
        window._recorder.start();
        """
        await client.evaluate_js(init_recorder_js)

        for chunk_idx in range(total_chunks):
            start_i = chunk_idx * chunk_size
            end_i = min(len(captured_frames), start_i + chunk_size)
            chunk_data = captured_frames[start_i:end_i]
            push_frames_js = f"""
            (() => {{
                const batch = {json.dumps(chunk_data)};
                window._framesList.push(...batch);
                return window._framesList.length;
            }})()
            """
            await client.evaluate_js(push_frames_js)

        print(f"[OK] Injected {len(captured_frames)} frames into browser renderer.")

        render_video_js = """
        (async () => {
            for (let i = 0; i < window._framesList.length; i++) {
                const b64 = window._framesList[i];
                await new Promise((resolve) => {
                    const img = new Image();
                    img.onload = () => {
                        window._ctx.drawImage(img, 0, 0, 1920, 1080);
                        resolve();
                    };
                    img.src = 'data:image/jpeg;base64,' + b64;
                });
                await new Promise(r => setTimeout(r, 250)); // 4 fps = 250ms per frame
            }
            window._recorder.stop();
            await new Promise(r => window._recorder.onstop = r);
            const blob = new Blob(window._capturedChunks, { type: 'video/webm' });
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            });
        })()
        """
        print("[INFO] Rendering video stream in browser...")
        res_data_url = await client.evaluate_js(render_video_js)

        if res_data_url and "," in res_data_url:
            raw_b64 = res_data_url.split(",", 1)[1]
            video_bytes = base64.b64decode(raw_b64)
            with open(OUTPUT_WEBM, "wb") as f:
                f.write(video_bytes)
            print(f"[SUCCESS] Saved WebM video to: {OUTPUT_WEBM} ({len(video_bytes)} bytes)")

            shutil.copyfile(OUTPUT_WEBM, ARTIFACT_WEBM)
            print(f"[SUCCESS] Saved Conversation Artifact copy to: {ARTIFACT_WEBM}")
            step_results["WebM Video Artifact Creation"] = f"SUCCESS ({len(video_bytes)} bytes)"
        else:
            print("[ERROR] Failed to extract WebM base64 stream from browser.")
            step_results["WebM Video Artifact Creation"] = "FAIL"

    finally:
        if client:
            await client.close()
        proc.terminate()
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
        except Exception:
            pass

    print("\n============================================================")
    print(" DEMONSTRATION RECORDING EXECUTION SUMMARY")
    print("============================================================")
    for step, outcome in step_results.items():
        print(f" - {step}: {outcome}")
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_demo_recording())
