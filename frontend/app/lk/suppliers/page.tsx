"use client";
import { useEffect, useState } from "react";
import { getSuppliers, getMe, api } from "@/lib/api";
import { IconTruck, IconSearch, IconPlus } from "@/components/icons";

const MODERATION_LABELS: Record<string, { text: string; cls: string }> = {
  verified: { text: "Подтверждён", cls: "bg-green-100 text-green-700" },
  unverified: { text: "На проверке", cls: "bg-orange-100 text-orange-700" },
  rejected: { text: "Отклонён", cls: "bg-red-100 text-red-700" },
};

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [isStaff, setIsStaff] = useState(false);
  const [moderationFilter, setModerationFilter] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCats, setSelectedCats] = useState<Set<number>>(new Set());
  const [addForm, setAddForm] = useState({ name: "", email: "", phone: "", site: "", city: "", address: "", supplier_type: "unknown" });
  const [addError, setAddError] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [notice, setNotice] = useState("");

  const load = (params?: Record<string, string>) => {
    setLoading(true);
    getSuppliers(params)
      .then((data) => setSuppliers(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    getMe().then((me) => setIsStaff(!!me.is_staff)).catch(() => {});
    api("/suppliers/categories/").then((data) => setCategories(data.results || data)).catch(() => {});
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (city) params.city = city;
    if (moderationFilter) params.moderation_status = moderationFilter;
    load(params);
  };

  // B4: staff moderation
  const moderate = async (id: number, status: string) => {
    try {
      await api("/suppliers/" + id + "/moderate/", { method: "POST", body: JSON.stringify({ status }) });
      setSuppliers(suppliers.map((s) => (s.id === id ? { ...s, moderation_status: status } : s)));
      setNotice(status === "verified" ? "Поставщик подтверждён" : status === "rejected" ? "Поставщик отклонён — исключён из подбора" : "Статус обновлён");
      setTimeout(() => setNotice(""), 4000);
    } catch (e: any) {
      setNotice("Ошибка модерации: " + e.message);
    }
  };

  // B5: manual supplier add
  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError("");
    setAddLoading(true);
    try {
      await api("/suppliers/", {
        method: "POST",
        body: JSON.stringify({
          name: addForm.name,
          email: addForm.email,
          phone: addForm.phone,
          site: addForm.site,
          supplier_type: addForm.supplier_type,
          address: addForm.address,
          categories: Array.from(selectedCats),
        }),
      });
      setNotice("Поставщик «" + addForm.name + "» добавлен и уже участвует в подборе");
      setTimeout(() => setNotice(""), 5000);
      setShowAddForm(false);
      setAddForm({ name: "", email: "", phone: "", site: "", city: "", address: "", supplier_type: "unknown" });
      setSelectedCats(new Set());
      load();
    } catch (e: any) {
      setAddError(e.message);
    } finally {
      setAddLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1a1a2e]">Поставщики</h1>
          <p className="text-[#64748b] mt-1">База проверенных поставщиков стройматериалов</p>
        </div>
        <button onClick={() => setShowAddForm(!showAddForm)} className="flex items-center gap-2 px-5 py-3 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold hover:bg-[#fcc419] transition">
          <IconPlus className="w-4 h-4" /> Добавить поставщика
        </button>
      </div>

      {notice && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-800 rounded-xl text-sm">{notice}</div>}

      {showAddForm && (
        <form onSubmit={handleAdd} className="bg-white rounded-2xl border border-[#e2e8f0] p-6 mb-6">
          <h2 className="font-bold text-[#1a1a2e] mb-4">Новый поставщик</h2>
          {addError && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{addError}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input required value={addForm.name} onChange={(e) => setAddForm({ ...addForm, name: e.target.value })} placeholder="Название *" className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" />
            <input value={addForm.email} onChange={(e) => setAddForm({ ...addForm, email: e.target.value })} type="email" placeholder="Email" className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" />
            <input value={addForm.phone} onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })} placeholder="Телефон" className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" />
            <input value={addForm.site} onChange={(e) => setAddForm({ ...addForm, site: e.target.value })} placeholder="Сайт (https://...)" className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" />
            <input value={addForm.address} onChange={(e) => setAddForm({ ...addForm, address: e.target.value })} placeholder="Адрес (город, улица)" className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" />
            <select value={addForm.supplier_type} onChange={(e) => setAddForm({ ...addForm, supplier_type: e.target.value })} className="px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl text-sm">
              <option value="unknown">Тип: неизвестно</option>
              <option value="manufacturer">Производитель</option>
              <option value="dealer">Дилер</option>
            </select>
          </div>
          {categories.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-[#64748b] mb-2">Категории материалов:</p>
              <div className="flex flex-wrap gap-2">
                {categories.map((c: any) => (
                  <button type="button" key={c.id}
                    onClick={() => { const next = new Set(selectedCats); next.has(c.id) ? next.delete(c.id) : next.add(c.id); setSelectedCats(next); }}
                    className={"px-3 py-1 rounded-full text-xs font-medium border transition " + (selectedCats.has(c.id) ? "bg-[#1e3a5f] text-white border-[#1e3a5f]" : "bg-white text-[#64748b] border-[#e2e8f0] hover:border-[#1e3a5f]")}>
                    {c.name}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="mt-4 flex gap-3">
            <button type="submit" disabled={addLoading || !addForm.name.trim()} className="px-6 py-2.5 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] transition disabled:opacity-50">{addLoading ? "Сохраняем..." : "Сохранить"}</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="px-6 py-2.5 border border-[#e2e8f0] rounded-xl font-medium hover:bg-[#f5f7fa] transition">Отмена</button>
          </div>
        </form>
      )}

      <form onSubmit={handleSearch} className="bg-white rounded-2xl border border-[#e2e8f0] p-4 mb-6">
        <div className="flex gap-3 flex-wrap">
          <div className="flex-1 relative min-w-[200px]">
            <IconSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94a3b8]" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по названию..." className="w-full pl-12 pr-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          </div>
          <input value={city} onChange={(e) => setCity(e.target.value)}
            placeholder="Город" className="w-40 px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          <select value={moderationFilter} onChange={(e) => setModerationFilter(e.target.value)} className="px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl text-sm">
            <option value="">Любой статус</option>
            <option value="verified">Подтверждённые</option>
            <option value="unverified">На проверке</option>
            <option value="rejected">Отклонённые</option>
          </select>
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
          {suppliers.map((s: any) => {
            const mod = MODERATION_LABELS[s.moderation_status || "unverified"];
            return (
              <div key={s.id} className="bg-white p-5 rounded-xl border border-[#e2e8f0] hover:shadow-md transition">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-[#1a1a2e]">{s.name}</h3>
                  <span className={"inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold shrink-0 " + mod.cls}>{mod.text}</span>
                </div>
                <p className="text-sm text-[#64748b]">{s.city || s.email}</p>
                <p className="text-xs text-[#94a3b8] mt-1">{s.phone} | {s.email}</p>
                {isStaff && (
                  <div className="mt-3 flex gap-2">
                    {s.moderation_status !== "verified" && (
                      <button onClick={() => moderate(s.id, "verified")} className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-bold hover:bg-green-700 transition">Подтвердить</button>
                    )}
                    {s.moderation_status !== "rejected" && (
                      <button onClick={() => moderate(s.id, "rejected")} className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-xs font-bold hover:bg-red-200 transition">Отклонить</button>
                    )}
                    {s.moderation_status !== "unverified" && (
                      <button onClick={() => moderate(s.id, "unverified")} className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-200 transition">На проверку</button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
