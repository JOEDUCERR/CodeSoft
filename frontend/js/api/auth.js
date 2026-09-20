import { config } from "../config.js";
import { ApiError, mockWait, request } from "./client.js";
import { MOCK_USERS, publicUser } from "../../data/users.js";

function sessionToken() {
  try {
    const raw = localStorage.getItem(config.sessionKey);
    return raw ? JSON.parse(raw).token : null;
  } catch {
    return null;
  }
}

const EXTRA_USERS_KEY = "codesoft.store.users";

function extraUsers() {
  try {
    return JSON.parse(localStorage.getItem(EXTRA_USERS_KEY) || "[]");
  } catch {
    return [];
  }
}

function allUsers() {
  return [...MOCK_USERS, ...extraUsers()];
}

function findUser(email) {
  return allUsers().find((u) => u.email.toLowerCase() === email.toLowerCase());
}

export async function login({ email, password }) {
  if (config.useMock) {
    await mockWait();
    const user = findUser(email);
    if (!user || user.password !== password) {
      throw new ApiError("Invalid email or password.", {
        status: 401,
        code: "INVALID_CREDENTIALS",
      });
    }
    return {
      token: `demo.${user.id}`,
      user: publicUser(user),
      demo: true,
    };
  }
  return request("/auth/login", { method: "POST", body: { email, password } });
}

export async function register({ name, email, password }) {
  if (config.useMock) {
    await mockWait();
    if (findUser(email)) {
      throw new ApiError("An account with that email already exists.", {
        status: 409,
        code: "EMAIL_TAKEN",
      });
    }
    const record = {
      id: `u_${Date.now()}`,
      name,
      email,
      password,
      role: "user",
      solvedIds: [],
      attemptedIds: [],
    };
    const extras = extraUsers();
    extras.push(record);
    localStorage.setItem(EXTRA_USERS_KEY, JSON.stringify(extras));
    const user = publicUser(record);
    return { token: `demo.${user.id}`, user, demo: true };
  }
  return request("/auth/register", { method: "POST", body: { name, email, password } });
}

export async function loginWithGoogle() {
  if (config.useMock) {
    await mockWait();
    throw new ApiError(
      "Google sign-in is a UI placeholder. The backend must complete OAuth.",
      { status: 501, code: "OAUTH_NOT_CONNECTED" }
    );
  }
  return request("/auth/google", { method: "POST", body: {} });
}

export async function getMe() {
  if (config.useMock) {
    await mockWait();
    const token = sessionToken();
    if (!token) {
      throw new ApiError("Unauthorized.", { status: 401, code: "UNAUTHORIZED" });
    }
    const id = String(token).replace(/^demo\./, "");
    const user = allUsers().find((u) => u.id === id);
    if (!user) {
      return { id, name: "Demo user", email: "", role: "user", solvedIds: [], attemptedIds: [] };
    }
    return publicUser(user);
  }
  return request("/auth/me", { token: sessionToken() });
}
