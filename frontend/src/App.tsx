
import { type FormEvent, useCallback, useEffect, useState } from "react";
import {
  Shield, LayoutDashboard, ScanLine, History, KeyRound, ShieldCheck,
  ShieldAlert, Activity, ArrowRight, LockKeyhole, CircleDot,
  ChevronDown, Zap, Search, Bell, Settings2, Filter, X, Terminal, LogOut,
} from "lucide-react";
import "./App.css";

type Page = "Overview" | "Prompt Playground" | "Audit Logs" | "API Settings";
type AuthMode = "login" | "register";
type AuthStatus = "checking" | "signed-out" | "authenticated";
type FilterType = "ALL" | "SAFE" | "BLOCKED";
type HeaderMenu = "search" | "notifications" | "profile" | null;

const API_KEY_SESSION_STORAGE = "prompt-firewall-api-key";
const API_BASE_URL_SESSION_STORAGE = "prompt-firewall-api-base-url";

type Finding =
  | string
  | {
      category?: string;
      description?: string;
      [key: string]: unknown;
    };

type AnalysisResponse = {
  is_suspicious?: boolean;
  total_findings?: number;
  findings?: Finding[];
  risk_score?: number;
  risk_status?: string;
  detected_categories?: string[];
  ai_response?: string | null;
  message?: string;
};

type ApiErrorResponse = {
  detail?: unknown;
  message?: string;
};

type RegistrationResponse = {
  api_key: string;
};

type AuditLogRecord = {
  id: number;
  user_id: number;
  raw_prompt: string;
  sanitized_prompt: string | null;
  risk_status: string;
  block_reason: string | null;
  ai_response: string | null;
  created_at: string;
};

function formatApiDetail(data: ApiErrorResponse | null): string {
  if (!data) return "";

  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (data.detail && typeof data.detail === "object") {
    const detail = data.detail as Record<string, unknown>;
    if (typeof detail.message === "string") return detail.message;
  }
  return typeof data.message === "string" ? data.message : "";
}

function App() {
  const [page, setPage] = useState<Page>("Overview");
  const [authStatus, setAuthStatus] = useState<AuthStatus>(() =>
    window.sessionStorage.getItem(API_KEY_SESSION_STORAGE) ? "checking" : "signed-out"
  );
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [loginApiKey, setLoginApiKey] = useState("");
  const [registrationName, setRegistrationName] = useState("");
  const [registrationEmail, setRegistrationEmail] = useState("");
  const [registrationApiKey, setRegistrationApiKey] = useState("");
  const [registrationKeyVisible, setRegistrationKeyVisible] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState(() =>
    window.sessionStorage.getItem(API_BASE_URL_SESSION_STORAGE) || "http://127.0.0.1:8000"
  );
  const [apiKey, setApiKey] = useState(() =>
    window.sessionStorage.getItem(API_KEY_SESSION_STORAGE) || ""
  );
  const [filter, setFilter] = useState<FilterType>("ALL");
  const [search, setSearch] = useState("");
  const [auditLogs, setAuditLogs] = useState<AuditLogRecord[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState("");
  const [selectedAuditLog, setSelectedAuditLog] = useState<AuditLogRecord | null>(null);
  const [keyVisible, setKeyVisible] = useState(false);
  const [headerMenu, setHeaderMenu] = useState<HeaderMenu>(null);

  const isAuthenticated = authStatus === "authenticated";
  const nav = [
    { name: "Overview" as Page, icon: LayoutDashboard },
    { name: "Prompt Playground" as Page, icon: ScanLine },
    { name: "Audit Logs" as Page, icon: History },
    { name: "API Settings" as Page, icon: KeyRound },
  ];

  const goTo = (nextPage: Page) => {
    setPage(nextPage);
    setHeaderMenu(null);
  };

  const updateApiBaseUrl = (value: string) => {
    setApiBaseUrl(value);
    window.sessionStorage.setItem(API_BASE_URL_SESSION_STORAGE, value);
  };

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!loginApiKey.trim() || !apiBaseUrl.trim()) {
      setAuthError("Enter both the backend URL and your API key.");
      return;
    }

    setAuthLoading(true);
    setAuthError("");
    try {
      const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
      const response = await fetch(`${baseUrl}/api/v1/prompt/connection-test`, {
        method: "GET",
        headers: { "X-API-Key": loginApiKey.trim() },
      });

      if (response.ok) {
        const verifiedKey = loginApiKey.trim();
        window.sessionStorage.setItem(API_KEY_SESSION_STORAGE, verifiedKey);
        setApiKey(verifiedKey);
        setLoginApiKey("");
        setAuthStatus("authenticated");
        setPage("Overview");
      } else if (response.status === 401 || response.status === 403) {
        setAuthError("Invalid API key. Check the key and try again.");
      } else {
        const data = await response.json().catch(() => null) as ApiErrorResponse | null;
        const message = formatApiDetail(data);
        setAuthError(
          message
            ? `Backend error (HTTP ${response.status}): ${message}`
            : `Unable to sign in (HTTP ${response.status}).`
        );
      }
    } catch {
      setAuthError("Could not reach the backend. Check the backend URL and CORS configuration.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegistration = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!registrationName.trim() || !registrationEmail.trim() || !apiBaseUrl.trim()) {
      setAuthError("Enter your name, email, and backend URL.");
      return;
    }

    setAuthLoading(true);
    setAuthError("");
    try {
      const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
      const response = await fetch(`${baseUrl}/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: registrationName.trim(),
          email: registrationEmail.trim(),
        }),
      });
      const data = await response.json().catch(() => null) as
        (ApiErrorResponse & Partial<RegistrationResponse>) | null;

      if (response.status === 201 && typeof data?.api_key === "string" && data.api_key) {
        setRegistrationApiKey(data.api_key);
        setRegistrationName("");
        setRegistrationEmail("");
        setRegistrationKeyVisible(false);
        setAuthError("");
      } else if (response.status === 409) {
        setAuthError("An account with this email already exists. Sign in with its API key.");
      } else {
        const message = formatApiDetail(data);
        setAuthError(
          message
            ? `Could not create account (HTTP ${response.status}): ${message}`
            : `Could not create account (HTTP ${response.status}).`
        );
      }
    } catch {
      setAuthError("Could not reach the backend. Check the backend URL and CORS configuration.");
    } finally {
      setAuthLoading(false);
    }
  };

  const continueAfterRegistration = () => {
    if (!registrationApiKey) return;
    window.sessionStorage.setItem(API_KEY_SESSION_STORAGE, registrationApiKey);
    setApiKey(registrationApiKey);
    setRegistrationApiKey("");
    setAuthStatus("authenticated");
    setPage("Overview");
  };

  const handleLogout = () => {
    window.sessionStorage.removeItem(API_KEY_SESSION_STORAGE);
    setApiKey("");
    setAuthStatus("signed-out");
    setAuthMode("login");
    setLoginApiKey("");
    setRegistrationApiKey("");
    setAuthError("");
    setPage("Overview");
    setPrompt("");
    setSearch("");
    setFilter("ALL");
    setAuditLogs([]);
    setAuditError("");
    setSelectedAuditLog(null);
    setAnalysis(null);
    setResult(false);
    setErrorMessage("");
    setConnectionStatus("");
    setRegistrationName("");
    setRegistrationEmail("");
  };

  const openLogs = (type: FilterType = "ALL", query = "") => {
    setFilter(type);
    setSearch(query);
    goTo("Audit Logs");
  };

  useEffect(() => {
    if (authStatus !== "checking") return;
    let active = true;

    const verifySavedSession = async () => {
      const savedKey = window.sessionStorage.getItem(API_KEY_SESSION_STORAGE);
      if (!savedKey) {
        setAuthStatus("signed-out");
        return;
      }

      try {
        const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
        const response = await fetch(`${baseUrl}/api/v1/prompt/connection-test`, {
          method: "GET",
          headers: { "X-API-Key": savedKey },
        });
        if (!active) return;

        if (response.ok) {
          setAuthStatus("authenticated");
        } else {
          window.sessionStorage.removeItem(API_KEY_SESSION_STORAGE);
          setApiKey("");
          setAuthError(
            response.status === 401 || response.status === 403
              ? "Your saved API key is no longer valid. Sign in again."
              : `Could not verify the saved session (HTTP ${response.status}). Sign in again.`
          );
          setAuthStatus("signed-out");
        }
      } catch {
        if (!active) return;
        window.sessionStorage.removeItem(API_KEY_SESSION_STORAGE);
        setApiKey("");
        setAuthError("Could not reach the backend to verify your saved session. Sign in again.");
        setAuthStatus("signed-out");
      }
    };

    void verifySavedSession();
    return () => {
      active = false;
    };
  }, [apiBaseUrl, authStatus]);

  const loadAuditLogs = useCallback(async () => {
    if (!apiKey.trim()) {
      setAuditLogs([]);
      setAuditError("Enter your API key in API Settings before loading audit logs.");
      return;
    }
    if (!apiBaseUrl.trim()) {
      setAuditLogs([]);
      setAuditError("Enter your backend API base URL in API Settings.");
      return;
    }

    setAuditLoading(true);
    setAuditError("");

    try {
      const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
      const response = await fetch(`${baseUrl}/api/v1/prompt/audit-logs?limit=100`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey.trim(),
        },
      });
      const data = await response.json().catch(() => null);

      if (response.status === 200 && Array.isArray(data)) {
        setAuditLogs(data as AuditLogRecord[]);
      } else if (response.status === 401) {
        setAuditLogs([]);
        setAuditError("Authentication failed. The API key is invalid.");
      } else if (response.status === 403) {
        setAuditLogs([]);
        setAuditError("Access denied. The API key does not have permission to view audit logs.");
      } else {
        const message = formatApiDetail(data as ApiErrorResponse);
        setAuditLogs([]);
        setAuditError(
          message
            ? `Failed to load audit logs (HTTP ${response.status}): ${message}`
            : `Failed to load audit logs (HTTP ${response.status}).`
        );
      }
    } catch {
      setAuditLogs([]);
      setAuditError(
        "Connection error. Unable to reach the backend. Check the API URL and FastAPI CORS configuration."
      );
    } finally {
      setAuditLoading(false);
    }
  }, [apiBaseUrl, apiKey]);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (page !== "Overview" && page !== "Audit Logs") return;
    const timer = window.setTimeout(() => {
      void loadAuditLogs();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [isAuthenticated, page, loadAuditLogs]);

  const safeAuditLogCount = auditLogs.filter(
    (log) => log.risk_status.toUpperCase() === "SAFE"
  ).length;
  const blockedAuditLogCount = auditLogs.filter(
    (log) => log.risk_status.toUpperCase() === "BLOCKED"
  ).length;
  const blockRate = auditLogs.length
    ? (blockedAuditLogCount / auditLogs.length) * 100
    : 0;
  const blockedAuditLogs = auditLogs.filter(
    (log) => log.risk_status.toUpperCase() === "BLOCKED"
  );
  const overviewCategories = auditLogs.reduce<Map<string, number>>((categories, log) => {
    for (const finding of parseBlockReason(log.block_reason)) {
      const label =
        typeof finding === "string"
          ? finding
          : finding.category || finding.description || "Security finding";
      categories.set(label, (categories.get(label) || 0) + 1);
    }
    return categories;
  }, new Map());

  const filteredAuditLogs = auditLogs.filter((log) => {
    const matchesFilter =
      filter === "ALL" ||
      log.risk_status.toUpperCase() === filter;
    const haystack = [
      `EV-${log.id}`,
      log.risk_status,
      log.raw_prompt,
      log.sanitized_prompt || "",
      log.block_reason || "",
    ].join(" ").toLowerCase();
    return matchesFilter && haystack.includes(search.toLowerCase());
  });

  const formatAuditTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleString();
  };

  function parseBlockReason(blockReason: string | null): Finding[] {
    if (!blockReason) return [];
    try {
      const parsed: unknown = JSON.parse(blockReason);
      return Array.isArray(parsed) ? parsed as Finding[] : [];
    } catch {
      return [];
    }
  }

  const analyzePrompt = async (promptToAnalyze: string): Promise<Response> => {
    const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
    return fetch(`${baseUrl}/api/v1/prompt/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey.trim(),
      },
      body: JSON.stringify({ prompt: promptToAnalyze }),
    });
  };

  const scanPrompt = async () => {
    if (!prompt.trim() || analysisLoading) return;

    if (!apiKey.trim()) {
      setResult(true);
      setAnalysis(null);
      setErrorMessage("Enter your API key in API Settings before analyzing prompts.");
      return;
    }
    if (!apiBaseUrl.trim()) {
      setResult(true);
      setAnalysis(null);
      setErrorMessage("Enter your backend API base URL in API Settings.");
      return;
    }

    setAnalysisLoading(true);
    setResult(false);
    setAnalysis(null);
    setErrorMessage("");

    try {
      const response = await analyzePrompt(prompt.trim());
      const data = await response.json().catch(() => null) as ApiErrorResponse | AnalysisResponse | null;

      if (response.status === 200) {
        setAnalysis(data as AnalysisResponse);
        setResult(true);
      } else if (response.status === 403) {
        const responseData = data as ApiErrorResponse & AnalysisResponse;
        const detail = responseData.detail;
        const blockedAnalysis =
          detail && typeof detail === "object" && !Array.isArray(detail)
            ? detail as AnalysisResponse
            : responseData as AnalysisResponse;

        setAnalysis({
          ...blockedAnalysis,
          risk_status: blockedAnalysis.risk_status || "BLOCKED",
        });
        setResult(true);
      } else if (response.status === 401) {
        setErrorMessage("Authentication failed. The API key is invalid.");
        setResult(true);
      } else if (response.status === 422) {
        const message = formatApiDetail(data as ApiErrorResponse);
        setErrorMessage(message ? `Validation error: ${message}` : "Validation error. The prompt is invalid.");
        setResult(true);
      } else {
        const message = formatApiDetail(data as ApiErrorResponse);
        setErrorMessage(
          message
            ? `Backend error (HTTP ${response.status}): ${message}`
            : `Backend error (HTTP ${response.status}).`
        );
        setResult(true);
      }
    } catch {
      setErrorMessage(
        "Connection error. Unable to reach the backend. Check that FastAPI is running, the URL is correct, and CORS is configured."
      );
      setResult(true);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const testConnection = async () => {
    if (!apiKey.trim()) {
      setConnectionStatus("Please enter your API key first.");
      return;
    }
    if (!apiBaseUrl.trim()) {
      setConnectionStatus("Please enter your API base URL first.");
      return;
    }

    setAnalysisLoading(true);
    setConnectionStatus("Testing backend connection...");
    try {
      const baseUrl = apiBaseUrl.trim().replace(/\/+$/, "");
      const response = await fetch(`${baseUrl}/api/v1/prompt/connection-test`, {
        method: "GET",
        headers: {
          "X-API-Key": apiKey.trim(),
        },
      });
      const data = await response.json().catch(() => null) as ApiErrorResponse | null;

      if (response.ok) {
        window.sessionStorage.setItem(API_KEY_SESSION_STORAGE, apiKey.trim());
        setConnectionStatus(
          typeof data?.message === "string"
            ? data.message
            : "Successful authenticated connection. API key accepted and backend responded."
        );
      } else if (response.status === 401 || response.status === 403) {
        setConnectionStatus(`Invalid API key or insufficient authorization (HTTP ${response.status}).`);
      } else if (response.status >= 500) {
        const message = formatApiDetail(data);
        setConnectionStatus(
          message
            ? `Backend unavailable (HTTP ${response.status}): ${message}`
            : `Backend unavailable (HTTP ${response.status}).`
        );
      } else {
        const message = formatApiDetail(data);
        setConnectionStatus(
          message
            ? `Backend error (HTTP ${response.status}): ${message}`
            : `Backend error (HTTP ${response.status}).`
        );
      }
    } catch {
      setConnectionStatus(
        "Connection failure. Check the backend URL, ensure FastAPI is running, and verify CORS settings."
      );
    } finally {
      setAnalysisLoading(false);
    }
  };

  const clearAnalysis = () => {
    setResult(false);
    setAnalysis(null);
    setErrorMessage("");
  };

  const renderAnalysis = () => (
    result && (
      <div className="demo-result">
        {errorMessage ? (
          <>
            <div className="demo-result-header"><ShieldAlert size={17} /><strong>Request error</strong></div>
            <p>{errorMessage}</p>
          </>
        ) : analysis ? (
          <>
            <div className="demo-result-header">
              {analysis.risk_status?.toUpperCase() === "SAFE"
                ? <ShieldCheck size={17} />
                : <ShieldAlert size={17} />}
              <strong>Analysis result · {analysis.risk_status || "Analyzed"}</strong>
            </div>

            <div className="analysis-stats">
              <div><small>Risk score</small><strong>{analysis.risk_score ?? "N/A"}/100</strong></div>
              <div><small>Status</small><strong>{analysis.risk_status || "N/A"}</strong></div>
              <div><small>Findings</small><strong>{analysis.total_findings ?? analysis.findings?.length ?? 0}</strong></div>
              <div><small>Suspicious</small><strong>{analysis.is_suspicious === undefined ? "N/A" : analysis.is_suspicious ? "Yes" : "No"}</strong></div>
            </div>

            {analysis.detected_categories && analysis.detected_categories.length > 0 && (
              <div className="analysis-categories">
                <strong>Detected categories</strong>
                <div className="category-chips">
                  {analysis.detected_categories.map((category, index) => (
                    <span key={`${category}-${index}`}>{category}</span>
                  ))}
                </div>
              </div>
            )}

            {analysis.findings && analysis.findings.length > 0 && (
              <div className="analysis-findings">
                <strong>Findings</strong>
                {analysis.findings.map((finding, index) => (
                  <div className="finding-item" key={index}>
                    {typeof finding === "string" ? finding : (
                      <>
                        {finding.category && <strong>{finding.category}</strong>}
                        {finding.description && <p>{finding.description}</p>}
                        {!finding.category && !finding.description && <pre>{JSON.stringify(finding, null, 2)}</pre>}
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}

            {analysis.ai_response && (
              <div className="analysis-response">
                <strong>AI response</strong>
                <p>{analysis.ai_response}</p>
              </div>
            )}
          </>
        ) : null}
        <button className="text-button" onClick={clearAnalysis}>Clear result <X size={14} /></button>
      </div>
    )
  );

  if (!isAuthenticated) {
    return (
      <main className="auth-page">
        <section className="auth-card" aria-labelledby="auth-title">
          <div className="auth-brand">
            <div className="brand-icon"><Shield size={21} /></div>
            <div>
              <strong>Prompt Firewall</strong>
              <span>AI SECURITY LAYER</span>
            </div>
          </div>

          {authStatus === "checking" ? (
            <div className="auth-checking" role="status">Checking saved session...</div>
          ) : registrationApiKey ? (
            <div className="auth-key-screen">
              <div className="auth-eyebrow">ACCOUNT CREATED</div>
              <h1 id="auth-title">Save your API key</h1>
              <p className="auth-copy">
                This key is shown only once by the backend. Save it if you need to sign in again.
              </p>
              <label htmlFor="new-account-api-key">Generated API key</label>
              <div className="auth-secret-field">
                <input
                  id="new-account-api-key"
                  className="auth-input"
                  type={registrationKeyVisible ? "text" : "password"}
                  value={registrationApiKey}
                  readOnly
                  onFocus={(event) => event.currentTarget.select()}
                />
                <button
                  className="auth-reveal-button"
                  type="button"
                  onClick={() => setRegistrationKeyVisible((visible) => !visible)}
                >
                  {registrationKeyVisible ? "Hide" : "Show"}
                </button>
              </div>
              <p className="auth-note">Click the field to select the key, then copy it.</p>
              <button className="analyze-button auth-submit" type="button" onClick={continueAfterRegistration}>
                Continue to dashboard <ArrowRight size={14} />
              </button>
            </div>
          ) : (
            <>
              <div className="auth-eyebrow">{authMode === "login" ? "SECURE WORKSPACE" : "NEW WORKSPACE"}</div>
              <h1 id="auth-title">{authMode === "login" ? "Welcome back" : "Create your account"}</h1>
              <p className="auth-copy">
                {authMode === "login"
                  ? "Sign in with the API key generated for your account."
                  : "Create an account to receive your API key."}
              </p>

              {authError && <div className="auth-error" role="alert">{authError}</div>}

              <div className="auth-url-field">
                <label htmlFor="auth-api-base-url">Backend API URL</label>
                <input
                  id="auth-api-base-url"
                  className="auth-input"
                  type="url"
                  required
                  value={apiBaseUrl}
                  onChange={(event) => updateApiBaseUrl(event.target.value)}
                  placeholder="http://127.0.0.1:8000"
                />
              </div>

              {authMode === "login" ? (
                <form className="auth-form" onSubmit={handleLogin}>
                  <label htmlFor="login-api-key">API key</label>
                  <input
                    id="login-api-key"
                    className="auth-input"
                    type="password"
                    autoComplete="off"
                    required
                    value={loginApiKey}
                    onChange={(event) => setLoginApiKey(event.target.value)}
                    placeholder="Paste your generated API key"
                  />
                  <button className="analyze-button auth-submit" type="submit" disabled={authLoading}>
                    {authLoading ? "Signing in..." : "Log in"} <ArrowRight size={14} />
                  </button>
                </form>
              ) : (
                <form className="auth-form" onSubmit={handleRegistration}>
                  <label htmlFor="register-name">Name</label>
                  <input
                    id="register-name"
                    className="auth-input"
                    type="text"
                    autoComplete="name"
                    minLength={2}
                    maxLength={100}
                    required
                    value={registrationName}
                    onChange={(event) => setRegistrationName(event.target.value)}
                    placeholder="Your name"
                  />
                  <label htmlFor="register-email">Email</label>
                  <input
                    id="register-email"
                    className="auth-input"
                    type="email"
                    autoComplete="email"
                    minLength={5}
                    maxLength={254}
                    required
                    value={registrationEmail}
                    onChange={(event) => setRegistrationEmail(event.target.value)}
                    placeholder="you@example.com"
                  />
                  <button className="analyze-button auth-submit" type="submit" disabled={authLoading}>
                    {authLoading ? "Creating account..." : "Create account"} <ArrowRight size={14} />
                  </button>
                </form>
              )}

              <div className="auth-switch">
                {authMode === "login" ? "Need an account?" : "Already have an account?"}
                <button
                  type="button"
                  disabled={authLoading}
                  onClick={() => {
                    setAuthMode(authMode === "login" ? "register" : "login");
                    setAuthError("");
                  }}
                >
                  {authMode === "login" ? "Create account" : "Log in"}
                </button>
              </div>
              <p className="auth-note">Authentication uses your backend-generated API key. No password is collected.</p>
            </>
          )}
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Shield size={21} /></div>
          <div>
            <h1>Prompt Firewall</h1>
            <span className="brand-subtitle">AI SECURITY LAYER</span>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list">
          {nav.map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`nav-item ${page === name ? "active" : ""}`}
              onClick={() => goTo(name)}
            >
              <Icon size={18} />
              <span>{name}</span>
              {name === "Audit Logs" && <span className="nav-count">{auditLogs.length}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="upgrade-card">
            <Zap size={16} className="upgrade-icon" />
            <p>Firewall engine</p>
            <span>Backend integration status</span>
            <div className="upgrade-status">
              <span className={`status-dot ${apiKey ? "" : "offline-dot"}`} />
              {apiKey ? "API key configured" : "Offline · Ready to connect"}
            </div>
            <button className="engine-connect-link" onClick={() => goTo("API Settings")}>
              Connect API <ArrowRight size={13} />
            </button>
          </div>

          <div className="profile">
            <div className="avatar">VP</div>
            <div className="profile-info">
              <strong>Workspace Admin</strong>
              <span>Local workspace</span>
            </div>
            <ChevronDown size={16} className="profile-chevron" />
          </div>
          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={15} /> Log out
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-slash">/</span>
            <strong>{page}</strong>
          </div>

          <div className="topbar-right">
            <div className="system-status">
              <span className="status-dot" /> UI running
            </div>

            {/* Header search */}
            <div className="header-menu-wrap">
              <button
                className={`icon-button ${headerMenu === "search" ? "menu-active" : ""}`}
                onClick={() => setHeaderMenu(headerMenu === "search" ? null : "search")}
                title="Search events"
                aria-label="Search events"
              >
                <Search size={17} />
              </button>

              {headerMenu === "search" && (
                <div className="header-popover search-popover">
                  <div className="popover-title">
                    <strong>Search audit logs</strong>
                    <button className="popover-close" onClick={() => setHeaderMenu(null)}><X size={15} /></button>
                  </div>
                  <div className="audit-search popover-search">
                    <Search size={15} />
                    <input
                      autoFocus
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && openLogs(filter, search)}
                      placeholder="Search events, ID, category..."
                    />
                    {search && <button onClick={() => setSearch("")}><X size={14} /></button>}
                  </div>
                  <button className="popover-action" onClick={() => openLogs(filter, search)}>
                    View search results <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </div>

            {/* Notifications */}
            <div className="header-menu-wrap">
              <button
                className={`icon-button notification-button ${headerMenu === "notifications" ? "menu-active" : ""}`}
                onClick={() => setHeaderMenu(headerMenu === "notifications" ? null : "notifications")}
                title="Notifications"
                aria-label="Notifications"
              >
                <Bell size={17} />
                {blockedAuditLogs.length > 0 && <span className="notification-dot" />}
              </button>

              {headerMenu === "notifications" && (
                <div className="header-popover notification-popover">
                  <div className="popover-title">
                    <strong>Recent alerts</strong>
                    <span className="popover-count">{blockedAuditLogs.length}</span>
                    <button className="popover-close" onClick={() => setHeaderMenu(null)}><X size={15} /></button>
                  </div>
                  {blockedAuditLogs.slice(0, 5).map((log) => (
                    <button className="notification-item" key={log.id} onClick={() => { setHeaderMenu(null); setSelectedAuditLog(log); }}>
                      <span className="event-dot blocked" />
                      <span className="notification-item-text">
                        <strong>Blocked prompt · EV-{log.id}</strong>
                        <small>{formatAuditTimestamp(log.created_at)} · {log.raw_prompt}</small>
                      </span>
                      <ArrowRight size={14} />
                    </button>
                  ))}
                  {!auditLoading && !auditError && blockedAuditLogs.length === 0 && (
                    <div className="empty-state">No blocked records in the fetched audit data.</div>
                  )}
                  {auditLoading && <div className="empty-state">Loading alerts...</div>}
                  {auditError && <div className="empty-state">{auditError}</div>}
                  <button className="popover-action" onClick={() => openLogs("BLOCKED")}>
                    View blocked events <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </div>

            {/* Profile menu */}
            <div className="header-menu-wrap">
              <button
                className={`top-avatar ${headerMenu === "profile" ? "menu-active" : ""}`}
                onClick={() => setHeaderMenu(headerMenu === "profile" ? null : "profile")}
                title="Workspace profile"
                aria-label="Workspace profile"
              >
                VP
              </button>

              {headerMenu === "profile" && (
                <div className="header-popover profile-popover">
                  <div className="profile-popover-head">
                    <div className="avatar">VP</div>
                    <div>
                      <strong>Workspace Admin</strong>
                      <small>Local workspace</small>
                    </div>
                  </div>
                  <button className="popover-menu-item" onClick={() => goTo("Overview")}><LayoutDashboard size={15} /> Dashboard</button>
                  <button className="popover-menu-item" onClick={() => goTo("API Settings")}><Settings2 size={15} /> API Settings</button>
                  <div className="popover-footnote">Prompt Firewall · Local UI</div>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="page-content">
          {page === "Overview" && <>
            <section className="page-heading">
              <div>
                <div className="eyebrow"><CircleDot size={13} /> SECURITY CONSOLE</div>
                <h2>Overview</h2>
                <p>Metrics reflect the latest up to 100 audit records returned by the API.</p>
              </div>
              <button className="date-button" onClick={() => goTo("Prompt Playground")}>
                <Activity size={15} /> Run a test <ArrowRight size={14} />
              </button>
            </section>

            <section className="metrics-grid">
              <button className="metric-card clickable" onClick={() => openLogs("ALL")}>
                <div className="metric-top"><span>Prompts analyzed (fetched)</span><div className="metric-icon purple"><ScanLine size={17} /></div></div>
                <div className="metric-value">{auditLoading ? "..." : auditError ? "—" : auditLogs.length}</div>
                <div className="metric-footer">View fetched records <ArrowRight size={13}/></div>
              </button>

              <button className="metric-card clickable" onClick={() => openLogs("BLOCKED")}>
                <div className="metric-top"><span>BLOCKED prompts</span><div className="metric-icon red"><ShieldAlert size={17} /></div></div>
                <div className="metric-value">{auditLoading ? "..." : auditError ? "—" : blockedAuditLogCount}</div>
                <div className="metric-footer">Filter blocked records <ArrowRight size={13}/></div>
              </button>

              <button className="metric-card clickable" onClick={() => openLogs("SAFE")}>
                <div className="metric-top"><span>SAFE prompts</span><div className="metric-icon green"><ShieldCheck size={17} /></div></div>
                <div className="metric-value">{auditLoading ? "..." : auditError ? "—" : safeAuditLogCount}</div>
                <div className="metric-footer">Filter safe records <ArrowRight size={13}/></div>
              </button>

              <button className="metric-card clickable" onClick={() => openLogs("BLOCKED")}>
                <div className="metric-top"><span>Block rate (fetched)</span><div className="metric-icon orange"><Activity size={17} /></div></div>
                <div className="metric-value">{auditLoading ? "..." : auditError ? "—" : `${blockRate.toFixed(1)}%`}</div>
                <div className="metric-footer">BLOCKED / fetched records <ArrowRight size={13}/></div>
              </button>
            </section>

            <section className="playground-section">
              <div className="section-heading">
                <div><h3>Quick prompt test</h3><p>Try a prompt in the playground.</p></div>
                <button className="text-button" onClick={() => goTo("Prompt Playground")}>Full playground <ArrowRight size={15} /></button>
              </div>

              <div className="playground-card">
                <div className="playground-card-top">
                  <div className="playground-title">
                    <div className="playground-icon"><ScanLine size={17} /></div>
                    <div className="playground-title-text">
                      <strong>Prompt inspection</strong>
                        <span>Frontend preview · Not sent to server</span>
                    </div>
                  </div>
                    <div className="mode-pill"><span /> PREVIEW</div>
                </div>

                <textarea
                  value={prompt}
                  onChange={(e) => { setPrompt(e.target.value); clearAnalysis(); }}
                    placeholder="Paste a prompt to prepare a test..."
                  rows={4}
                />

                <div className="playground-footer">
                    <span className="input-hint"><LockKeyhole size={13}/> No data sent yet</span>
                    <button className="analyze-button" onClick={() => { setAnalysis(null); setErrorMessage(""); setResult(true); }} disabled={!prompt.trim()}>
                    <ScanLine size={15}/> Inspect prompt
                  </button>
                </div>

                {result && <div className="demo-result">
                    <div className="demo-result-header"><Terminal size={17}/><strong>Preview only</strong></div>
                    <p>Your input is ready for API integration. This preview does not classify threats or send requests.</p>
                    <button className="text-button" onClick={() => goTo("API Settings")}>Configure backend <ArrowRight size={14}/></button>
                </div>}
              </div>
            </section>

            <section className="bottom-grid">
              <div className="panel">
                <div className="section-heading">
                  <div><h3>Detected findings</h3><p>From fetched audit records · Select to filter</p></div>
                </div>
                {auditLoading && <div className="empty-state">Loading audit data...</div>}
                {!auditLoading && auditError && <div className="empty-state">{auditError}</div>}
                {!auditLoading && !auditError && overviewCategories.size === 0 && (
                  <div className="empty-state">
                    {auditLogs.length === 0 ? "No audit records returned." : "No findings are available in these audit records."}
                  </div>
                )}
                {!auditLoading && !auditError && Array.from(overviewCategories.entries()).map(([category, count]) => (
                  <button className="category-row" key={category} onClick={() => openLogs("ALL", category)}>
                    <span className="category-name">{category}</span>
                    <span className="category-count">{count}<ArrowRight size={13}/></span>
                  </button>
                ))}
              </div>

              <div className="panel">
                <div className="section-heading">
                  <div><h3>Recent activity</h3><p>Latest records from fetched audit data</p></div>
                  <button className="text-button" onClick={loadAuditLogs} disabled={auditLoading}>
                    {auditLoading ? "Refreshing..." : "Refresh"} <ArrowRight size={14}/>
                  </button>
                  <button className="text-button" onClick={() => openLogs("ALL")}>View logs <ArrowRight size={14}/></button>
                </div>
                {auditLoading && <div className="empty-state">Loading recent activity...</div>}
                {!auditLoading && auditError && <div className="empty-state">{auditError}</div>}
                {!auditLoading && !auditError && auditLogs.length === 0 && (
                  <div className="empty-state">No audit activity found.</div>
                )}
                {!auditLoading && !auditError && auditLogs.slice(0, 3).map(log => (
                  <button className="event-preview" key={log.id} onClick={() => setSelectedAuditLog(log)}>
                    <span className={`event-dot ${log.risk_status.toLowerCase()}`}/>
                    <span className="event-preview-text">
                      <strong>{log.risk_status} · EV-{log.id}</strong>
                      <small>{log.raw_prompt} · {formatAuditTimestamp(log.created_at)}</small>
                    </span>
                    <ArrowRight size={14}/>
                  </button>
                ))}
              </div>
            </section>
          </>}

          {page === "Prompt Playground" && <>
            <section className="page-heading">
              <div><div className="eyebrow"><ScanLine size={13}/> TEST LAB</div><h2>Prompt Playground</h2><p>Analyze prompts with the live security backend.</p></div>
            </section>

            <div className="playground-card full-playground">
              <div className="playground-card-top">
                <div className="playground-title">
                  <div className="playground-icon"><ScanLine size={17}/></div>
                  <div className="playground-title-text">
                    <strong>Prompt analyzer</strong>
                    <span>{apiKey ? "Backend authentication configured" : "Configure API key to connect"}</span>
                  </div>
                </div>
                <div className="mode-pill"><span/> LIVE</div>
              </div>

              <textarea
                value={prompt}
                onChange={(e) => {setPrompt(e.target.value);clearAnalysis();}}
                placeholder="Enter your prompt here..."
                rows={8}
              />

              <div className="playground-footer">
                <span className="input-hint">{prompt.length} characters · Live analysis</span>
                <button className="analyze-button" onClick={scanPrompt} disabled={!prompt.trim() || analysisLoading}>
                  {analysisLoading ? "Analyzing..." : "Analyze prompt"} <ArrowRight size={14}/>
                </button>
              </div>

              {renderAnalysis()}
            </div>
          </>}

          {page === "Audit Logs" && <>
            <section className="page-heading">
              <div><div className="eyebrow"><History size={13}/> EVENT MONITOR</div><h2>Audit Logs</h2><p>Inspect authenticated prompt security records.</p></div>
              <button className="text-button" onClick={loadAuditLogs} disabled={auditLoading}>
                {auditLoading ? "Loading..." : "Refresh"} <ArrowRight size={14}/>
              </button>
            </section>

            <div className="panel audit-panel">
              <div className="audit-controls">
                <div className="audit-search">
                  <Search size={15}/>
                  <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search prompts, ID, status..."/>
                  {search && <button aria-label="Clear search" onClick={() => setSearch("")}><X size={14}/></button>}
                </div>
                <div className="filter-buttons">
                  <Filter size={15}/>
                  {(["ALL","SAFE","BLOCKED"] as FilterType[]).map(f => (
                    <button className={filter===f?"selected":""} key={f} onClick={() => setFilter(f)}>{f}</button>
                  ))}
                </div>
              </div>

              <div className="audit-table">
                <div className="audit-header"><span>Event</span><span>Type</span><span>Risk</span><span>Time</span></div>
                {auditLoading && <div className="empty-state">Loading audit logs...</div>}
                {!auditLoading && auditError && <div className="empty-state">{auditError}</div>}
                {!auditLoading && !auditError && filteredAuditLogs.map(log => (
                  <button className="audit-row" key={log.id} onClick={() => setSelectedAuditLog(log)}>
                    <span className="audit-event">
                      <strong>EV-{log.id}</strong>
                      <small>{log.raw_prompt}</small>
                    </span>
                    <span className={`audit-badge ${log.risk_status.toLowerCase()}`}>{log.risk_status}</span>
                    <span className="risk-score">N/A</span>
                    <span className="audit-time">{formatAuditTimestamp(log.created_at)}</span>
                  </button>
                ))}
                {!auditLoading && !auditError && filteredAuditLogs.length===0 && (
                  <div className="empty-state">No audit logs match your filter.</div>
                )}
              </div>
            </div>
          </>}

          {page === "API Settings" && <>
            <section className="page-heading">
              <div><div className="eyebrow"><KeyRound size={13}/> CONFIGURATION</div><h2>API Settings</h2><p>Connection configuration for your local firewall backend.</p></div>
            </section>

            <div className="panel settings-panel">
              <h3>Backend connection</h3>
              <label>API base URL</label>
              <input
                className="settings-input"
                value={apiBaseUrl}
                onChange={(e) => {updateApiBaseUrl(e.target.value); setConnectionStatus("");}}
                placeholder="http://127.0.0.1:8000"
              />
              <label>API key</label>
              <div className="key-field">
                <input
                  type={keyVisible ? "text" : "password"}
                  placeholder="Paste your generated API key"
                  value={apiKey}
                  onChange={(e) => {setApiKey(e.target.value); setConnectionStatus("");}}
                />
                <button onClick={() => setKeyVisible(v => !v)}>{keyVisible?"Hide":"Show"}</button>
              </div>
              <div className="settings-hint"><ShieldCheck size={16}/> API key is kept in this browser tab's session and cleared on logout.</div>
              <button className="analyze-button" onClick={testConnection} disabled={analysisLoading}>
                {analysisLoading ? "Testing..." : "Test connection"} <ArrowRight size={14}/>
              </button>
              {connectionStatus && <div className="connection-message">{connectionStatus}</div>}
            </div>
          </>}

          <footer className="page-footer">
            <span>Prompt Firewall · Security middleware</span>
            <span>{page === "Overview" || page === "Audit Logs" ? "AUDIT DATA · Latest up to 100 API records" : "UI MODE · Preview"}</span>
          </footer>
        </div>
      </main>

      {selectedAuditLog && (
        <div className="modal-backdrop" onClick={() => setSelectedAuditLog(null)}>
          <div className="event-modal" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedAuditLog(null)}><X size={17}/></button>
            <div className="eyebrow"><History size={13}/> AUDIT LOG DETAIL</div>
            <h2>EV-{selectedAuditLog.id}</h2>
            <span className={`audit-badge ${selectedAuditLog.risk_status.toLowerCase()}`}>
              {selectedAuditLog.risk_status}
            </span>
            <dl>
              <dt>Timestamp</dt><dd>{formatAuditTimestamp(selectedAuditLog.created_at)}</dd>
              <dt>Risk score</dt><dd>Not provided by the audit logs API</dd>
              <dt>Prompt</dt><dd className="modal-prompt">{selectedAuditLog.raw_prompt}</dd>
              {selectedAuditLog.sanitized_prompt && (
                <><dt>Sanitized prompt</dt><dd className="modal-prompt">{selectedAuditLog.sanitized_prompt}</dd></>
              )}
              {selectedAuditLog.block_reason && (
                <>
                  <dt>Block reason / findings</dt>
                  <dd className="modal-prompt">
                    {parseBlockReason(selectedAuditLog.block_reason).length > 0
                      ? parseBlockReason(selectedAuditLog.block_reason).map((finding, index) => (
                          <span key={index}>
                            {typeof finding === "string"
                              ? finding
                              : finding.category || finding.description
                                ? `${finding.category ? `${finding.category}: ` : ""}${finding.description || ""}`
                                : JSON.stringify(finding)}
                            {index < parseBlockReason(selectedAuditLog.block_reason).length - 1 ? <br /> : null}
                          </span>
                        ))
                      : selectedAuditLog.block_reason}
                  </dd>
                </>
              )}
              {selectedAuditLog.ai_response && (
                <><dt>AI response</dt><dd className="modal-prompt">{selectedAuditLog.ai_response}</dd></>
              )}
            </dl>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;