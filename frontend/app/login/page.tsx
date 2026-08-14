"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Loader2 } from "lucide-react";

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
import { IconHardHat } from "@/components/icons";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Введите email")
    .email("Некорректный email адрес"),
  password: z.string().min(1, "Введите пароль"),
});

type LoginForm = z.infer<typeof loginSchema>;

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
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-ground)] px-4 py-8 relative">
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-[var(--radius-lg)] bg-[var(--sidebar-bg)] mb-4 shadow-[var(--shadow-medium)]">
            <IconHardHat className="w-7 h-7 text-[var(--accent)]" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--label-primary)]">
            Вход в Минитендер
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            Войдите, чтобы управлять заявками
          </p>
        </div>

        <Card className="shadow-[var(--shadow-medium)]">
          <CardHeader className="text-center">
            <CardTitle className="text-lg">Авторизация</CardTitle>
            <CardDescription>
              Введите email и пароль от вашего аккаунта
            </CardDescription>
          </CardHeader>
          <CardContent>
            {serverError && (
              <div
                className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm"
                role="alert"
                aria-live="assertive"
              >
                {serverError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email">Email</Label>
                <Input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.ru"
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
                  <Label htmlFor="login-password">Пароль</Label>
                  <a
                    href="#"
                    className="text-xs text-[var(--label-tertiary)] hover:text-[var(--accent)]"
                  >
                    Забыли пароль?
                  </a>
                </div>
                <Input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
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

              <Button
                type="submit"
                size="lg"
                className="w-full"
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

            <div className="mt-6 pt-6 border-t border-[var(--separator)] text-center">
              <p className="text-sm text-[var(--label-tertiary)]">
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