"use client";
import { useEffect, useState } from "react";
import { getSuppliers } from "@/lib/api";
import { IconTruck, IconSearch } from "@/components/icons";

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");

  const load = (params?: Record<string, string>) => {
    setLoading(true);
    getSuppliers(params)
      .then((data) => setSuppliers(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (city) params.city = city;
    load(params);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Поставщики</h1>
        <p className="text-[#64748b] mt-1">База проверенных поставщиков стройматериалов</p>
      </div>

      <form onSubmit={handleSearch} className="bg-white rounded-2xl border border-[#e2e8f0] p-4 mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <IconSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94a3b8]" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по названию..." className="w-full pl-12 pr-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          </div>
          <input value={city} onChange={(e) => setCity(e.target.value)}
            placeholder="Город" className="w-40 px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          <button type="submit" className="px-6 py-3 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] transition">Найти</button>
        </div>
      </form>

      {loading ? (
        <div className="text-[#64748b] p-8">Загрузка...</div>
      ) : suppliers.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
            <IconTruck className="w-10 h-10 text-[#1e3a5f]" />
          </div>
          <h2 className="text-xl font-bold text-[#1a1a2e] mb-2">Поставщики не найдены</h2>
          <p className="text-[#64748b]">Создайте заявку — система автоматически найдёт поставщиков в радиусе объекта.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suppliers.map((s: any) => (
            <div key={s.id} className="bg-white p-5 rounded-xl border border-[#e2e8f0] hover:shadow-md transition">
              <h3 className="font-bold text-[#1a1a2e]">{s.name}</h3>
              <p className="text-sm text-[#64748b]">{s.city || s.email}</p>
              <p className="text-xs text-[#94a3b8] mt-1">{s.phone} | {s.email}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
