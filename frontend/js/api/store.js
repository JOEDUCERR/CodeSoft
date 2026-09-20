import { config } from "../config.js";

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function write(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

export const store = {
  getProblemsOverlay() {
    return read(config.storeKeys.problems, null);
  },
  setProblemsOverlay(problems) {
    write(config.storeKeys.problems, problems);
  },
  getExtraSubmissions() {
    return read(config.storeKeys.submissions, []);
  },
  addSubmission(submission) {
    const list = this.getExtraSubmissions();
    list.unshift(submission);
    write(config.storeKeys.submissions, list);
  },
  getProfileOverlay() {
    return read(config.storeKeys.profile, {});
  },
  setProfileOverlay(profile) {
    write(config.storeKeys.profile, profile);
  },
};
