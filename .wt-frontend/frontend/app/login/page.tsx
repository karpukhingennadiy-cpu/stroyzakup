"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { IconHardHat } from "@/components/icons";
import { Button, Field } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/lk/requests");
    } catch (err: any) {
      setError(err.message || "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-ground px-4 py-8">
      <div className="fixed top-4 right-4">
        <span className="[&_button]:text-[var(--label-secondary)] [&_button:hover]:bg-[var(--fill-1)]">
          <ThemeToggle />
        </span>
      </div>
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-[var(--radius-xl)] bg-brand-sidebar mb-4 shadow-small">
            <IconHardHat className="w-8 h-8 text-brand" />
          </div>
          <h1 className="text-xl font-semibold text-label-1">Вход в Минитендер</h1>
          <p className="text-label-3 text-sm mt-1">Войдите, чтобы управлять заявками</p>
        </div>

        <div className="surface-card p-8">
          {error && (
            <div className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm" role="alert">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Field
              id="login-email" label="Email" type="email" required
              autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.ru"
            />
            <Field
              id="login-password" label="Пароль" type="password" required
              autoComplete="current-password"
              value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
            <Button type="submit" variant="primary" size={44} loading={loading} className="w-full">
              {loading ? "Вход..." : "Войти"}
            </Button>
          </form>
          <div className="mt-6 pt-6 border-t border-separator text-center">
            <p className="text-sm text-label-3">
              Нет аккаунта? <Link href="/register" className="text-[var(--accent)] font-medium hover:underline">Зарегистрироваться</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
