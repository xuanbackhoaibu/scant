export const DEMO_LOGIN = Object.freeze({
  email: "demo@aireportstudio.pro",
  password: "DemoVIP123!",
});

export function getDemoLoginPayload() {
  return { ...DEMO_LOGIN };
}
