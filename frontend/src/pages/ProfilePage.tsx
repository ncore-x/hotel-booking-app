import { useState, useEffect, useRef, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { useT } from "../i18n/useT";
import { useNotificationStore } from "../stores/notificationStore";

const CITIZENSHIPS = [
  "Россия", "Беларусь", "Казахстан", "Украина", "Узбекистан",
  "Азербайджан", "Грузия", "Армения", "Кыргызстан", "Таджикистан",
  "Молдова", "Туркменистан", "Латвия", "Литва", "Эстония",
  "Германия", "Франция", "Великобритания", "США", "Другое",
];

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, fetchMe, isLoading } = useAuthStore();
  const t = useT();
  const p = t.profilePage;
  const addNotification = useNotificationStore((s) => s.add);

  // Profile fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [citizenship, setCitizenship] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "">("");
  const [phone, setPhone] = useState("");
  const [profileMsg, setProfileMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Avatar
  const avatarInputRef = useRef<HTMLInputElement>(null);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);

  // Password fields
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");

  const [passwordMsg, setPasswordMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [emailMsg, setEmailMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) navigate("/login");
  }, [user, isLoading, navigate]);

  // Pre-fill from user data
  useEffect(() => {
    if (user) {
      setFirstName(user.first_name ?? "");
      setLastName(user.last_name ?? "");
      setBirthDate(user.birth_date ?? "");
      setCitizenship(user.citizenship ?? "");
      setGender((user.gender as "male" | "female" | "") ?? "");
      setPhone(user.phone ?? "");
    }
  }, [user]);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setAvatarError(null);
    setAvatarLoading(true);
    try {
      await authApi.uploadAvatar(file);
      await fetchMe();
    } catch (err) {
      setAvatarError(err instanceof ApiError ? err.detail : "Не удалось загрузить фото");
    } finally {
      setAvatarLoading(false);
    }
  };

  const handleAvatarDelete = async () => {
    setAvatarError(null);
    setAvatarLoading(true);
    try {
      await authApi.deleteAvatar();
      await fetchMe();
    } catch {
      setAvatarError("Не удалось удалить фото");
    } finally {
      setAvatarLoading(false);
    }
  };

  const handleProfileSave = async (e: FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    setProfileLoading(true);
    try {
      const updated = await authApi.updateProfile({
        first_name: firstName || null,
        last_name: lastName || null,
        birth_date: birthDate || null,
        citizenship: citizenship || null,
        gender: gender || null,
        phone: phone || null,
      });
      await fetchMe();
      setProfileMsg({ text: p.profileSuccess, ok: true });
      // Sync local state with returned data
      setFirstName(updated.first_name ?? "");
      setLastName(updated.last_name ?? "");
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : p.profileError;
      setProfileMsg({ text: msg, ok: false });
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ text: p.passwordMismatch, ok: false });
      return;
    }
    setPasswordLoading(true);
    try {
      await authApi.updatePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMsg({ text: p.passwordSent, ok: true });
      addNotification(
        "password_sent",
        t.notifications.passwordSentTitle,
        t.notifications.passwordSentBody,
      );
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : p.passwordError;
      setPasswordMsg({ text: msg, ok: false });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleEmailChange = async (e: FormEvent) => {
    e.preventDefault();
    setEmailMsg(null);
    setEmailLoading(true);
    const targetEmail = newEmail;
    try {
      await authApi.updateEmail({ new_email: targetEmail, current_password: emailPassword });
      setEmailMsg({ text: p.emailSent(targetEmail), ok: true });
      addNotification(
        "email_sent",
        t.notifications.emailSentTitle,
        t.notifications.emailSentBody(targetEmail),
      );
      setNewEmail("");
      setEmailPassword("");
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : p.emailError;
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
          {p.title}
        </h1>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Account info sidebar */}
        <div className="lg:col-span-1">
          <div className="rounded-2xl border border-divider bg-card p-6">
            {/* Avatar */}
            <input
              ref={avatarInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarUpload}
            />
            <div className="mb-4 flex flex-col items-center gap-3">
              <div className="relative">
                <div className="h-20 w-20 overflow-hidden rounded-full border-2 border-divider bg-secondary">
                  {avatarLoading ? (
                    <div className="flex h-full w-full items-center justify-center">
                      <Spinner size="sm" />
                    </div>
                  ) : user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt="Avatar"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-brand/10">
                      <span className="text-2xl font-bold text-brand">
                        {(user.first_name?.[0] ?? user.email[0]).toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
                {/* Upload button overlay */}
                <button
                  onClick={() => avatarInputRef.current?.click()}
                  disabled={avatarLoading}
                  className="absolute bottom-0 right-0 flex h-7 w-7 items-center justify-center rounded-full border-2 border-card bg-brand text-on-brand shadow transition-colors hover:bg-brand-hv disabled:opacity-50"
                  title="Загрузить фото"
                >
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>

              {user.avatar_url && (
                <button
                  onClick={handleAvatarDelete}
                  disabled={avatarLoading}
                  className="text-xs text-muted transition-colors hover:text-fail disabled:opacity-50"
                >
                  Удалить фото
                </button>
              )}
              {avatarError && (
                <p className="text-center text-xs text-fail">{avatarError}</p>
              )}
            </div>

            {(user.first_name || user.last_name) && (
              <p className="font-semibold text-ink text-center">
                {[user.first_name, user.last_name].filter(Boolean).join(" ")}
              </p>
            )}
            <p className="text-xs font-semibold uppercase tracking-wider text-muted mt-3">{t.login.email}</p>
            <p className="mt-1 text-sm font-medium text-ink break-all">{user.email}</p>
            {user.is_admin && (
              <span className="mt-3 inline-flex items-center rounded-full bg-brand px-3 py-1 text-xs font-medium text-on-brand">
                Administrator
              </span>
            )}
          </div>
        </div>

        {/* Forms column */}
        <div className="space-y-6 lg:col-span-2">

          {/* ── Profile settings ── */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-1 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {p.profileSettings}
            </h2>
            <p className="mb-6 text-sm text-muted">{p.profileSubtitle}</p>

            <form onSubmit={handleProfileSave} className="space-y-4">
              {/* Last name + First name */}
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={p.lastName}
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Иванов"
                />
                <Input
                  label={p.firstName}
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Иван"
                />
              </div>

              {/* Birth date + Citizenship */}
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={p.birthDate}
                  type="date"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                />
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-ink">{p.citizenship}</label>
                  <select
                    value={citizenship}
                    onChange={(e) => setCitizenship(e.target.value)}
                    className="rounded-xl border border-divider bg-surface px-3 py-2.5 text-sm text-ink focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                  >
                    <option value="">{p.citizenship}</option>
                    {CITIZENSHIPS.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Gender */}
              <div className="flex items-center gap-6">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-ink">
                  <input
                    type="radio"
                    name="gender"
                    value="male"
                    checked={gender === "male"}
                    onChange={() => setGender("male")}
                    className="accent-brand h-4 w-4"
                  />
                  {p.genderMale}
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-sm text-ink">
                  <input
                    type="radio"
                    name="gender"
                    value="female"
                    checked={gender === "female"}
                    onChange={() => setGender("female")}
                    className="accent-brand h-4 w-4"
                  />
                  {p.genderFemale}
                </label>
              </div>

              {/* Phone + Email (readonly) */}
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={p.phone}
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+71234567890"
                />
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <label className="text-sm font-medium text-ink">{p.emailReadonly}</label>
                    <span title={p.emailReadonlyHint} className="flex h-4 w-4 items-center justify-center rounded-full border border-divider text-[10px] text-muted cursor-default">i</span>
                  </div>
                  <div className="rounded-xl border border-divider bg-secondary px-3 py-2.5 text-sm text-muted select-none truncate">
                    {user.email}
                  </div>
                </div>
              </div>

              {profileMsg && (
                <p className={`text-sm ${profileMsg.ok ? "text-green-600" : "text-fail"}`}>
                  {profileMsg.text}
                </p>
              )}

              <button
                type="submit"
                disabled={profileLoading}
                className="rounded-xl bg-brand px-6 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
              >
                {profileLoading ? "…" : p.save}
              </button>
            </form>
          </div>

          {/* ── Linked accounts ── */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-1 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {p.linkedAccounts}
            </h2>
            <p className="mb-5 text-sm text-muted">{p.linkedAccountsSubtitle}</p>

            <div className="space-y-3">
              {/* Password */}
              <div className="flex items-center justify-between rounded-xl border border-divider px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary">
                    <svg className="h-4 w-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink">{p.passwordMethod}</p>
                    <p className="text-xs text-muted">{p.passwordMethodDesc}</p>
                  </div>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  user.has_password
                    ? "bg-green-500/10 text-green-600 dark:text-green-400"
                    : "bg-secondary text-muted"
                }`}>
                  {user.has_password ? p.connected : p.notConnected}
                </span>
              </div>

              {/* Google */}
              <div className="flex items-center justify-between rounded-xl border border-divider px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary">
                    <svg className="h-4 w-4" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink">{p.googleMethod}</p>
                    <p className="text-xs text-muted">{p.googleMethodDesc}</p>
                  </div>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  user.oauth_provider === "google"
                    ? "bg-green-500/10 text-green-600 dark:text-green-400"
                    : "bg-secondary text-muted"
                }`}>
                  {user.oauth_provider === "google" ? p.connected : p.notConnected}
                </span>
              </div>


            </div>
          </div>

          {/* ── Change password ── */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-5 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {p.changePassword}
            </h2>
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <Input
                label={p.currentPassword}
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <Input
                label={p.newPassword}
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <Input
                label={p.confirmPassword}
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              {passwordMsg && (
                <p className={`text-sm ${passwordMsg.ok ? "text-green-600" : "text-fail"}`}>
                  {passwordMsg.text}
                </p>
              )}
              <button
                type="submit"
                disabled={passwordLoading}
                className="rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
              >
                {passwordLoading ? "…" : p.save}
              </button>
            </form>
          </div>

          {/* ── Change email ── */}
          <div className="rounded-2xl border border-divider bg-card p-6">
            <h2
              className="mb-5 text-lg font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {p.changeEmail}
            </h2>
            <form onSubmit={handleEmailChange} className="space-y-4">
              <Input
                label={p.newEmail}
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                required
              />
              <Input
                label={p.currentPassword}
                type="password"
                value={emailPassword}
                onChange={(e) => setEmailPassword(e.target.value)}
                required
              />
              {emailMsg && (
                <p className={`text-sm ${emailMsg.ok ? "text-green-600" : "text-fail"}`}>
                  {emailMsg.text}
                </p>
              )}
              <button
                type="submit"
                disabled={emailLoading}
                className="rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
              >
                {emailLoading ? "…" : p.save}
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}
