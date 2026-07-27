"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { IconHardHat } from "@/components/icons";

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f5f7fa] to-[#e8ecf1] px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#1e3a5f] mb-4 shadow-lg">
            <IconHardHat className="w-8 h-8 text-[#f0a500]" />
          </div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">Вход в Минитендер</h1>
          <p className="text-[#64748b] mt-1">Войдите, чтобы управлять заявками</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-lg border border-[#e2e8f0]">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition"
                placeholder="you@company.ru" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Пароль</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition"
                placeholder="••••••••" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3.5 bg-[#1e3a5f] text-white rounded-xl font-semibold text-base hover:bg-[#2d5a8e] hover:shadow-lg transition disabled:opacity-50">
              {loading ? "Вход..." : "Войти"}
            </button>
          </form>
          <div className="mt-6 pt-6 border-t border-[#e2e8f0] text-center">
            <p className="text-sm text-[#64748b]">
              Нет аккаунта? <Link href="/register" className="text-[#1e3a5f] font-semibold hover:text-[#2d5a8e]">Зарегистрироваться</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
