"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { HardHat, Loader2 } from "lucide-react";

import { login } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Введите email")
    .email("Некорректный email адрес"),
  password: z.string().min(1, "Введите пароль"),
});

type LoginForm = z.infer<typeof loginSchema>;

function GoogleIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  );
}

const fieldDark =
  "bg-[var(--bg-input-dark)] border-white/15 text-white placeholder:text-white/40 focus-visible:border-brand focus-visible:ring-brand/30 dark:bg-[var(--bg-input-dark)]";

export default function LoginPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: LoginForm) => {
    setServerError("");
    try {
      await login(data.email, data.password);
      router.push("/lk/requests");
    } catch (err: any) {
      setServerError(err.message || "Ошибка входа");
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center overflow-hidden bg-gradient-to-b from-[var(--bg-dark)] to-[#0f0f1e] px-4 py-8">
      {/* Декоративные янтарные круги */}
      <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand/10 blur-3xl pointer-events-none" aria-hidden="true" />
      <div className="absolute -bottom-40 -right-24 w-[28rem] h-[28rem] rounded-full bg-brand/10 blur-3xl pointer-events-none" aria-hidden="true" />

      <div className="fixed top-4 right-4 z-50 [&_button]:text-white/60 [&_button:hover]:bg-white/10">
        <ThemeToggle />
      </div>

      <div className="relative max-w-md w-full space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-[var(--radius-xl)] bg-white/5 ring-1 ring-white/10 mb-4 shadow-[var(--shadow-lg)]">
            <HardHat className="w-8 h-8 text-brand" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold text-white">
            Вход в Минитендер
          </h1>
          <p className="text-white/60 text-sm mt-1">
            Войдите, чтобы управлять заявками
          </p>
        </div>

        <Card className="bg-[var(--bg-dark-elevated)] border-white/10 shadow-[var(--shadow-lg)]">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg text-white">Авторизация</CardTitle>
            <CardDescription className="text-white/60">
              Введите email и пароль от вашего аккаунта
            </CardDescription>
          </CardHeader>
          <CardContent>
            {serverError && (
              <div
                className="mb-4 p-3 bg-[var(--danger-soft)] border border-white/10 text-[var(--danger)] rounded-[var(--radius-md)] text-sm"
                role="alert"
                aria-live="assertive"
              >
                {serverError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-white/70 text-sm font-medium">Email</Label>
                <Input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.ru"
                  className={fieldDark}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "login-email-error" : undefined}
                  {...register("email")}
                />
                {errors.email && (
                  <p id="login-email-error" className="text-sm text-[var(--danger)]">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="login-password" className="text-white/70 text-sm font-medium">Пароль</Label>
                  <Link href="#" className="text-sm text-[var(--accent)] hover:underline focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2 rounded-[var(--radius-xs)]">
                    Забыли пароль?
                  </Link>
                </div>
                <Input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={fieldDark}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "login-password-error" : undefined}
                  {...register("password")}
                />
                {errors.password && (
                  <p id="login-password-error" className="text-sm text-[var(--danger)]">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <label className="flex items-center gap-2 text-sm text-white/70 select-none cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded accent-[var(--brand)]" defaultChecked />
                Запомнить меня
              </label>

              <Button
                type="submit"
                variant="brand"
                className="w-full hover:-translate-y-px transition-transform"
                disabled={isSubmitting}
                aria-busy={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                    Вход...
                  </>
                ) : (
                  "Войти"
                )}
              </Button>
            </form>

            <div className="mt-6 flex items-center gap-3" aria-hidden="true">
              <div className="h-px flex-1 bg-white/10" />
              <span className="text-xs text-white/40">или</span>
              <div className="h-px flex-1 bg-white/10" />
            </div>

            <Button type="button" variant="ghost-dark" className="w-full mt-4">
              <GoogleIcon />
              Войти через Google
            </Button>

            <div className="mt-6 pt-6 border-t border-white/10 text-center">
              <p className="text-sm text-white/60">
                Нет аккаунта?{" "}
                <Link
                  href="/register"
                  className="text-[var(--accent)] font-medium hover:underline focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2 rounded-[var(--radius-xs)]"
                >
                  Зарегистрироваться
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
