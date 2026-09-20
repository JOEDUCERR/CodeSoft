import { config } from "../config.js";
import { mockWait, request } from "./client.js";
import { getCurrentUser } from "../auth.js";
import { listSubmissions } from "./submissions.js";

function token() {
  try {
    const raw = localStorage.getItem(config.sessionKey);
    return raw ? JSON.parse(raw).token : null;
  } catch {
    return null;
  }
}

export async function getProfile() {
  if (config.useMock) {
    await mockWait();
    const user = getCurrentUser();
    const submissions = await listSubmissions();
    const accepted = submissions.filter((s) => s.status === "Accepted");
    const solved = new Set(accepted.map((s) => s.problemId));
    const activity = Array.from({ length: 48 }, (_, i) => {
      const day = submissions.filter((s) => {
        const d = new Date(s.createdAt);
        const bucket = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24 * 2));
        return bucket === i % 16;
      });
      return Math.min(2, day.length);
    });
    return {
      name: user?.name || "User",
      email: user?.email || "",
      role: user?.role || "user",
      solved: solved.size,
      submissions: submissions.length,
      accepted: accepted.length,
      recent: submissions.slice(0, 8),
      activity,
    };
  }
  return request("/profile", { token: token() });
}
