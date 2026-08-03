"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser, login } from "@/lib/api";
import { IconHardHat } from "@/components/icons";
import { Button, Field } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await registerUser(form);
      await login(form.email, form.password);
      router.push("/lk/requests");
    } catch (err: any) {
      setError(err.message || "Ошибка регистрации");
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
          <h1 className="text-xl font-semibold text-label-1">Регистрация</h1>
          <p className="text-label-3 text-sm mt-1">Создайте аккаунт для доступа к сервису</p>
        </div>

        <div className="surface-card p-8">
          {error && (
            <div className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm" role="alert">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Field
              id="reg-email" label="Email" type="email" required
              autoComplete="email"
              value={form.email} onChange={update("email")}
              placeholder="you@company.ru"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field
                id="reg-first-name" label="Имя" type="text"
                autoComplete="given-name"
                value={form.first_name} onChange={update("first_name")}
              />
              <Field
                id="reg-last-name" label="Фамилия" type="text"
                autoComplete="family-name"
                value={form.last_name} onChange={update("last_name")}
              />
            </div>
            <Field
              id="reg-password" label="Пароль" type="password" required minLength={8}
              autoComplete="new-password"
              value={form.password} onChange={update("password")}
              placeholder="Минимум 8 символов"
            />
            <Button type="submit" variant="primary" size={44} loading={loading} className="w-full">
              {loading ? "Регистрация..." : "Зарегистрироваться"}
            </Button>
          </form>
          <div className="mt-6 pt-6 border-t border-separator text-center">
            <p className="text-sm text-label-3">
              Уже есть аккаунт? <Link href="/login" className="text-[var(--accent)] font-medium hover:underline">Войти</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
