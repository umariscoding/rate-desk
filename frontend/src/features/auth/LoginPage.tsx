import { type FormEvent, useState } from "react";

import { Notice } from "../../components/Notice";
import { useSession } from "../../hooks/useSession";
import { ROLE_LABEL } from "../../lib/session";

const DEMO_PASSWORD = "ratedesk";
const DEMO_ACCOUNTS = [
  { username: "umar", name: "Umar Azhar", role: "salesperson" as const },
  { username: "dorm", name: "DORM A", role: "dorm" as const },
];

export function LoginPage() {
  const { signIn } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(username, password);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Could not sign in");
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <h1 className="login__title">Rate Desk</h1>
      <p className="muted login__subtitle">Group sales for Hotel A, Lisbon</p>
      <form className="card card__body form" onSubmit={submit}>
        <h2 className="card__title">Sign in</h2>
        <label className="field">
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" autoFocus />
        </label>
        <label className="field">
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
        </label>
        {error && <Notice>{error}</Notice>}
        <div>
          <button className="btn btn--primary" type="submit" disabled={busy || username === "" || password === ""}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </div>
      </form>
      <section className="card login__demo" aria-label="Demo accounts">
        <header className="card__header">
          <h2 className="card__title">Demo accounts</h2>
          <span className="card__meta">Password for both: {DEMO_PASSWORD}</span>
        </header>
        <table className="list">
          <tbody>
            {DEMO_ACCOUNTS.map((account) => (
              <tr key={account.username}>
                <td>
                  <strong>{account.name}</strong>
                  <div className="muted">{ROLE_LABEL[account.role]}</div>
                </td>
                <td>{account.username}</td>
                <td>
                  <button
                    className="btn"
                    type="button"
                    onClick={() => {
                      setUsername(account.username);
                      setPassword(DEMO_PASSWORD);
                    }}
                  >
                    Fill in
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
