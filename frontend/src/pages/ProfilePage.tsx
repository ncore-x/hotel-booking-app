import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { Input } from "../components/ui/Input";
import { useT } from "../i18n/useT";

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, fetchMe, isLoading } = useAuthStore();
  const t = useT();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");

  const [passwordMsg, setPasswordMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [emailMsg, setEmailMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) navigate("/login");
  }, [user, isLoading, navigate]);

  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    setPasswordLoading(true);
    try {
      await authApi.updatePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMsg({ text: t.profilePage.passwordSuccess, ok: true });
      setCurrentPassword("");
      setNewPassword("");
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : t.profilePage.passwordError;
      setPasswordMsg({ text: msg, ok: false });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleEmailChange = async (e: FormEvent) => {
    e.preventDefault();
    setEmailMsg(null);
    setEmailLoading(true);
    try {
      await authApi.updateEmail({ new_email: newEmail, current_password: emailPassword });
      setEmailMsg({ text: t.profilePage.emailSuccess, ok: true });
      setNewEmail("");
      setEmailPassword("");
      await fetchMe();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : t.profilePage.emailError;
      setEmailMsg({ text: msg, ok: false });
    } finally {
      setEmailLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
      {/* Header */}
      <div className="mb-10 border-b border-divider pb-6">
        <h1
          className="text-4xl font-black uppercase tracking-tight text-ink"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {t.profilePage.title}
        </h1>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Account info */}
        <div className="lg:col-span-1">
          <div className="rounded-2xl border border-divider bg-card p-6">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
              <span className="text-xl font-bold text-muted">
                {user.email[0].toUpperCase()}
              </span>
            </div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.login.email}</p>
            <p className="mt-1 font-semibold text-ink">{user.email}</p>
            {user.is_admin && (
              <span className="mt-3 inline-flex items-center rounded-full bg-brand px-3 py-1 text-xs font-medium text-on-brand">
                Administrator
              </span>
            )}
          </div>
        </div>

        {/* Forms */}
        <div className="space-y-6 lg:col-span-2">
          {/* Change password */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-5 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {t.profilePage.changePassword}
            </h2>
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <Input
                label={t.profilePage.currentPassword}
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <Input
                label={t.profilePage.newPassword}
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              {passwordMsg && (
                <p className={`text-sm ${passwordMsg.ok ? "text-green-600" : "text-red-500"}`}>
                  {passwordMsg.text}
                </p>
              )}
              <button
                type="submit"
                disabled={passwordLoading}
                className="rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
              >
                {passwordLoading ? "…" : t.profilePage.save}
              </button>
            </form>
          </div>

          {/* Change email */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-5 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {t.profilePage.changeEmail}
            </h2>
            <form onSubmit={handleEmailChange} className="space-y-4">
              <Input
                label={t.profilePage.newEmail}
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                required
              />
              <Input
                label={t.profilePage.currentPassword}
                type="password"
                value={emailPassword}
                onChange={(e) => setEmailPassword(e.target.value)}
                required
              />
              {emailMsg && (
                <p className={`text-sm ${emailMsg.ok ? "text-green-600" : "text-red-500"}`}>
                  {emailMsg.text}
                </p>
              )}
              <button
                type="submit"
                disabled={emailLoading}
                className="rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
              >
                {emailLoading ? "…" : t.profilePage.save}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
