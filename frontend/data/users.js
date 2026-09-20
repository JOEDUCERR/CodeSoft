/** Demo accounts only. Not production credentials. */
export const MOCK_USERS = [
  {
    id: "u_demo",
    name: "Amlan",
    email: "demo@codesoft.dev",
    password: "demo-pass-1",
    role: "user",
    solvedIds: ["two-sum", "reverse-string", "binary-search", "climbing-stairs"],
    attemptedIds: ["valid-parentheses", "merge-intervals"],
  },
  {
    id: "u_admin",
    name: "Admin",
    email: "admin@codesoft.dev",
    password: "admin-pass-1",
    role: "admin",
    solvedIds: ["two-sum", "binary-search"],
    attemptedIds: ["two-sum"],
  },
];

export function publicUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    solvedIds: user.solvedIds || [],
    attemptedIds: user.attemptedIds || [],
  };
}
