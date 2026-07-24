"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser, login } from "@/lib/api";
import { IconHardHat } from "@/components/icons";

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f5f7fa] to-[#e8ecf1] px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#1e3a5f] mb-4 shadow-lg">
            <IconHardHat className="w-8 h-8 text-[#f0a500]" />
          </div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">Регистрация</h1>
          <p className="text-[#64748b] mt-1">Создайте аккаунт для доступа к сервису</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-lg border border-[#e2e8f0]">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Email</label>
              <input type="email" required value={form.email} onChange={update("email")}
                className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition"
                placeholder="you@company.ru" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Имя</label>
                <input type="text" value={form.first_name} onChange={update("first_name")}
                  className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Фамилия</label>
                <input type="text" value={form.last_name} onChange={update("last_name")}
                  className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Пароль</label>
              <input type="password" required minLength={8} value={form.password} onChange={update("password")}
                className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition"
                placeholder="Минимум 8 символов" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition disabled:opacity-50">
              {loading ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>
          <div className="mt-6 pt-6 border-t border-[#e2e8f0] text-center">
            <p className="text-sm text-[#64748b]">
              Уже есть аккаунт? <Link href="/login" className="text-[#1e3a5f] font-semibold hover:text-[#2d5a8e]">Войти</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
