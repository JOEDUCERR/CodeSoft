export function statusClass(status) {
  const s = (status || "").toLowerCase();
  if (s === "accepted" || s === "solved" || s === "published") return "badge badge-ok";
  if (s === "running" || s === "pending" || s === "draft") return "badge badge-warn";
  if (
    s.includes("error") ||
    s.includes("wrong") ||
    s.includes("exceeded") ||
    s === "failed"
  ) {
    return "badge badge-err";
  }
  return "badge badge-neutral";
}

export function difficultyClass(diff) {
  const d = (diff || "").toLowerCase();
  if (d === "easy") return "badge badge-easy";
  if (d === "medium") return "badge badge-medium";
  if (d === "hard") return "badge badge-hard";
  return "badge";
}

export function formatTime(iso) {
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min} min ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} hour${hr === 1 ? "" : "s"} ago`;
  const day = Math.floor(hr / 24);
  if (day < 14) return `${day} day${day === 1 ? "" : "s"} ago`;
  return d.toLocaleString();
}

export function formatMemory(kb) {
  if (!kb) return "—";
  if (kb < 1024) return `${kb} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function formatRuntime(ms) {
  if (!ms && ms !== 0) return "—";
  if (ms < 10) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}
