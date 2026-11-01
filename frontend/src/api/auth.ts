import { request } from "./http";
import type { Session } from "./types";

export const logIn = (username: string, password: string) =>
  request<Session>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
