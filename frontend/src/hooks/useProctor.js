import { useEffect, useState } from "react";
import { WS_BASE, getToken } from "../api";

const FRAME_INTERVAL_MS = 1500;

/**
 * Streams webcam frames to the backend and reports browser-side events
 * (tab switch, fullscreen exit, copy/paste). The next frame is only sent after the
 * server acknowledges the previous one, so a slow model never builds up a backlog.
 */
export function useProctor({ sessionId, videoRef, active, onViolation }) {
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    if (!active || !sessionId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/exam/${sessionId}?token=${getToken()}`);
    const canvas = document.createElement("canvas");
    let waitingSince = 0;
    let timer;

    const report = (event, detail = "") => {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ event, detail }));
    };

    const grabFrame = () => {
      const v = videoRef.current;
      const busy = waitingSince && Date.now() - waitingSince < 5000;
      if (!v || !v.videoWidth || busy || ws.readyState !== WebSocket.OPEN) return;
      canvas.width = 640;
      canvas.height = Math.round((640 * v.videoHeight) / v.videoWidth);
      canvas.getContext("2d").drawImage(v, 0, 0, canvas.width, canvas.height);
      waitingSince = Date.now();
      canvas.toBlob((b) => b && ws.send(b), "image/jpeg", 0.7);
    };

    ws.onopen = () => {
      setStatus("live");
      timer = setInterval(grabFrame, FRAME_INTERVAL_MS);
    };
    ws.onclose = () => {
      setStatus("closed");
      clearInterval(timer);
    };
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "ack") waitingSince = 0;
      if (msg.type === "violation") onViolation?.(msg);
    };

    const onVisibility = () => document.hidden && report("tab_switch", "Tab or window hidden");
    const onFullscreen = () => !document.fullscreenElement && report("fullscreen_exit", "Left fullscreen");
    const onClipboard = (e) => {
      e.preventDefault();
      report("copy_paste", e.type);
    };
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("fullscreenchange", onFullscreen);
    ["copy", "paste", "cut"].forEach((t) => document.addEventListener(t, onClipboard));

    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("fullscreenchange", onFullscreen);
      ["copy", "paste", "cut"].forEach((t) => document.removeEventListener(t, onClipboard));
      ws.close();
    };
  }, [active, sessionId]);

  return status;
}
