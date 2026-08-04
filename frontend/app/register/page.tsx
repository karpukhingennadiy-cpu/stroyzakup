"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { HardHat, Loader2 } from "lucide-react";

import { registerUser, login } from "@/lib/api";
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

const registerSchema = z.object({
  email: z
    .string()
    .min(1, "Введите email")
    .email("Некорректный email адрес"),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  password: z
    .string()
    .min(8, "Пароль должен содержать минимум 8 символов"),
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: RegisterForm) => {
    setServerError("");
    try {
      await registerUser(data);
      await login(data.email, data.password);
      router.push("/lk/requests");
    } catch (err: any) {
      setServerError(err.message || "Ошибка регистрации");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-ground)] px-4 py-8">
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-[var(--radius-xl)] bg-[var(--sidebar-bg)] mb-4 shadow-[var(--shadow-small)]">
            <HardHat className="w-8 h-8 text-[var(--brand)]" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold text-[var(--label-primary)]">
            Регистрация
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            Создайте аккаунт для доступа к сервису
          </p>
        </div>

        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">Новый аккаунт</CardTitle>
            <CardDescription>
              Заполните данные для регистрации
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
                <Label htmlFor="reg-email">Email</Label>
                <Input
                  id="reg-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.ru"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "reg-email-error" : undefined}
                  {...register("email")}
                />
                {errors.email && (
                  <p id="reg-email-error" className="text-sm text-[var(--danger)]">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="reg-first-name">Имя</Label>
                  <Input
                    id="reg-first-name"
                    type="text"
                    autoComplete="given-name"
                    placeholder="Иван"
                    {...register("first_name")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-last-name">Фамилия</Label>
                  <Input
                    id="reg-last-name"
                    type="text"
                    autoComplete="family-name"
                    placeholder="Иванов"
                    {...register("last_name")}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="reg-password">Пароль</Label>
                <Input
                  id="reg-password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Минимум 8 символов"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "reg-password-error" : undefined}
                  {...register("password")}
                />
                {errors.password && (
                  <p id="reg-password-error" className="text-sm text-[var(--danger)]">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting}
                aria-busy={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                    Регистрация...
                  </>
                ) : (
                  "Зарегистрироваться"
                )}
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-[var(--separator)] text-center">
              <p className="text-sm text-[var(--label-tertiary)]">
                Уже есть аккаунт?{" "}
                <Link
                  href="/login"
                  className="text-[var(--accent)] font-medium hover:underline focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2 rounded-[var(--radius-xs)]"
                >
                  Войти
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
