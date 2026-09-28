import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { LinkGenerator } from "./link-generator";
import { Management } from "./management";
import { DocumentManager } from "./document-manager";
import "./styles.css";
import "./workspace.css";
import "./management.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "daalgi_admin_token";
let authToken = "";

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof body.detail === "string" ? body.detail : `요청 실패 (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}

function AdminLogin({ onLogin, busy, error }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  return <main className="auth-shell"><section className="auth-card">
    <p className="eyebrow">Da-Al-G ADMIN</p>
    <h1>Da-Al-G 관리자</h1>
    <p className="subtitle">사용자 앱과 RAG 링크를 한곳에서 관리합니다.</p>
    {error && <div className="notice error" role="alert">{error}</div>}
    <form onSubmit={event => { event.preventDefault(); onLogin(username.trim(), password); }}>
      <label>아이디<input autoFocus value={username} onChange={event => setUsername(event.target.value)} /></label>
      <label>비밀번호<input type="password" value={password} onChange={event => setPassword(event.target.value)} /></label>
      <button className="primary-button" disabled={busy || !username.trim() || !password}>{busy ? "로그인 중…" : "로그인"}</button>
    </form>
  </section></main>;
}

const userSections = [["users", "회원"], ["documents", "문서"], ["duty", "근무표"],
  ["conversations", "대화"], ["bookmarks", "북마크"], ["feedback", "피드백"]];

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [sessionReady, setSessionReady] = useState(() => !token);
  const [user, setUser] = useState(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [area, setArea] = useState("user");
  const [section, setSection] = useState("users");

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    authToken = "";
    setToken("");
    setUser(null);
    setSessionReady(true);
  }

  async function logout() {
    try { if (token) await api("/api/auth/logout", { method: "POST" }); }
    catch (_) { /* Local session still ends if the server is unavailable. */ }
    finally { clearSession(); }
  }

  async function login(username, password) {
    setAuthBusy(true); setAuthError("");
    try {
      const body = await api("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }),
      });
      if (body.user?.role !== "admin") throw new Error("관리자 계정으로 로그인해 주세요.");
      localStorage.setItem(TOKEN_KEY, body.access_token);
      authToken = body.access_token;
      setUser(body.user);
      setToken(body.access_token);
      setSessionReady(true);
    } catch (reason) { setAuthError(reason.message); }
    finally { setAuthBusy(false); }
  }

  useEffect(() => {
    authToken = token;
    if (!token) { setUser(null); setSessionReady(true); return; }
    let gone = false;
    setSessionReady(false);
    api("/api/auth/me").then(me => {
      if (me.role !== "admin") throw new Error("관리자 권한이 없습니다.");
      if (!gone) { setUser(me); setSessionReady(true); }
    }).catch(reason => {
      if (!gone) { setAuthError(reason.message); clearSession(); }
    });
    return () => { gone = true; };
  }, [token]);

  if (!sessionReady) return <main className="auth-shell"><p>관리자 세션을 확인하는 중입니다…</p></main>;
  if (!user) return <AdminLogin onLogin={login} busy={authBusy} error={authError} />;

  return <main className="app-shell human-workspace admin-app">
    <header className="topbar"><div><p className="eyebrow">Da-Al-G ADMIN</p><h1>관리자</h1>
      <p className="subtitle">사용자 앱 운영과 RAG 근거 연결을 관리합니다.</p></div>
      <div className="pane-toolbar"><span>{user.display_name}</span><button onClick={logout}>로그아웃</button></div>
    </header>
    <nav className="admin-areas" aria-label="관리 영역">
      <button aria-current={area === "user" ? "page" : undefined} onClick={() => setArea("user")}>사용자 앱 관리</button>
      <button aria-current={area === "rag" ? "page" : undefined} onClick={() => setArea("rag")}>RAG 링크 관리</button>
    </nav>
    {area === "user" ? <>
      <nav className="workspace-tabs" aria-label="사용자 앱 관리 메뉴">
        {userSections.map(([value, label]) => <button key={value} aria-current={section === value ? "page" : undefined}
          onClick={() => setSection(value)}>{label}</button>)}
      </nav>
      {section === "documents" ? <DocumentManager api={api} /> : <Management section={section} api={api} />}
    </> : <LinkGenerator api={api} apiBase={API_BASE} token={token} user={user} onUnauthorized={clearSession} />}
  </main>;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
