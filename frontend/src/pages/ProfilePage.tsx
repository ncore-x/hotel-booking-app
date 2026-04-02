import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, fetchMe } = useAuthStore();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");

  const [passwordMsg, setPasswordMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [emailMsg, setEmailMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);

  useEffect(() => {
    if (!user) navigate("/login");
  }, [user, navigate]);

  const handlePasswordChange = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    setPasswordLoading(true);
    try {
      await authApi.updatePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMsg({ text: "Пароль успешно изменён", ok: true });
      setCurrentPassword("");
      setNewPassword("");
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : "Ошибка смены пароля";
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
      setEmailMsg({ text: "Email успешно изменён", ok: true });
      setNewEmail("");
      setEmailPassword("");
      await fetchMe();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : "Ошибка смены email";
      setEmailMsg({ text: msg, ok: false });
    } finally {
      setEmailLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Профиль</h1>

      <Card>
        <div className="space-y-2">
          <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
          <p className="font-medium text-gray-900 dark:text-white">{user.email}</p>
          {user.is_admin && (
            <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
              Администратор
            </span>
          )}
        </div>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Сменить пароль
        </h2>
        <form onSubmit={handlePasswordChange} className="space-y-3">
          <Input
            label="Текущий пароль"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Input
            label="Новый пароль"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          {passwordMsg && (
            <p className={`text-sm ${passwordMsg.ok ? "text-green-500" : "text-red-500"}`}>
              {passwordMsg.text}
            </p>
          )}
          <Button loading={passwordLoading}>Сменить пароль</Button>
        </form>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Сменить email
        </h2>
        <form onSubmit={handleEmailChange} className="space-y-3">
          <Input
            label="Новый email"
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            required
          />
          <Input
            label="Текущий пароль"
            type="password"
            value={emailPassword}
            onChange={(e) => setEmailPassword(e.target.value)}
            required
          />
          {emailMsg && (
            <p className={`text-sm ${emailMsg.ok ? "text-green-500" : "text-red-500"}`}>
              {emailMsg.text}
            </p>
          )}
          <Button loading={emailLoading}>Сменить email</Button>
        </form>
      </Card>
    </div>
  );
}
