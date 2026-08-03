"use client";
import { useEffect, useState } from "react";
import { getSuppliers, getMe, api } from "@/lib/api";
import { IconTruck, IconSearch, IconPlus } from "@/components/icons";
import { Button, Card, Badge, Field } from "@/components/ui";

const MODERATION_LABELS: Record<string, { text: string; tone: "success" | "warning" | "danger" }> = {
  verified: { text: "Подтверждён", tone: "success" },
  unverified: { text: "На проверке", tone: "warning" },
  rejected: { text: "Отклонён", tone: "danger" },
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
      <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-label-1">Поставщики</h1>
          <p className="text-label-3 text-sm mt-0.5">База проверенных поставщиков стройматериалов</p>
        </div>
        <Button variant="primary" size={44} onClick={() => setShowAddForm(!showAddForm)} leftIcon={<IconPlus className="w-5 h-5" />}>
          Добавить поставщика
        </Button>
      </div>

      {notice && (
        <div className="mb-4 p-3 bg-[var(--success-soft)] border border-[var(--separator)] text-[var(--success)] rounded-[var(--radius-lg)] text-sm" role="status">
          {notice}
        </div>
      )}

      {showAddForm && (
        <form onSubmit={handleAdd} className="surface-card p-6 mb-6">
          <h2 className="font-semibold text-label-1 mb-4">Новый поставщик</h2>
          {addError && (
            <div className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm" role="alert">
              {addError}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Field id="sup-name" label="Название *" required value={addForm.name} onChange={(e) => setAddForm({ ...addForm, name: e.target.value })} />
            <Field id="sup-email" label="Email" type="email" value={addForm.email} onChange={(e) => setAddForm({ ...addForm, email: e.target.value })} />
            <Field id="sup-phone" label="Телефон" value={addForm.phone} onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })} />
            <Field id="sup-site" label="Сайт" placeholder="https://..." value={addForm.site} onChange={(e) => setAddForm({ ...addForm, site: e.target.value })} />
            <Field id="sup-address" label="Адрес" placeholder="Город, улица" value={addForm.address} onChange={(e) => setAddForm({ ...addForm, address: e.target.value })} />
            <div>
              <label htmlFor="sup-type" className="block text-sm font-medium text-label-1 mb-1.5">Тип</label>
              <select id="sup-type" value={addForm.supplier_type} onChange={(e) => setAddForm({ ...addForm, supplier_type: e.target.value })} className="field-input">
                <option value="unknown">Неизвестно</option>
                <option value="manufacturer">Производитель</option>
                <option value="dealer">Дилер</option>
              </select>
            </div>
          </div>
          {categories.length > 0 && (
            <fieldset className="mt-4">
              <legend className="text-xs text-label-3 mb-2">Категории материалов:</legend>
              <div className="flex flex-wrap gap-2">
                {categories.map((c: any) => {
                  const active = selectedCats.has(c.id);
                  return (
                    <button type="button" key={c.id} aria-pressed={active}
                      onClick={() => { const next = new Set(selectedCats); active ? next.delete(c.id) : next.add(c.id); setSelectedCats(next); }}
                      className={"px-3 py-1.5 rounded-full text-xs font-medium border transition-colors duration-150 " +
                        (active ? "bg-[var(--label-primary)] text-[var(--bg-primary)] border-transparent" : "bg-transparent text-label-2 border-separator hover:bg-[var(--fill-1)]")}>
                      {c.name}
                    </button>
                  );
                })}
              </div>
            </fieldset>
          )}
          <div className="mt-4 flex gap-3">
            <Button type="submit" variant="primary" size={32} loading={addLoading} disabled={!addForm.name.trim()}>
              {addLoading ? "Сохраняем..." : "Сохранить"}
            </Button>
            <Button type="button" variant="outline" size={32} onClick={() => setShowAddForm(false)}>Отмена</Button>
          </div>
        </form>
      )}

      <form onSubmit={handleSearch} className="surface-card p-4 mb-6" role="search">
        <div className="flex gap-3 flex-wrap">
          <div className="flex-1 relative min-w-[200px]">
            <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-label-4" />
            <label htmlFor="supplier-search" className="sr-only">Поиск по названию</label>
            <input id="supplier-search" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по названию..." className="field-input pl-9" />
          </div>
          <label htmlFor="supplier-city" className="sr-only">Город</label>
          <input id="supplier-city" value={city} onChange={(e) => setCity(e.target.value)}
            placeholder="Город" className="field-input w-full sm:w-40" />
          <label htmlFor="supplier-moderation" className="sr-only">Статус модерации</label>
          <select id="supplier-moderation" value={moderationFilter} onChange={(e) => setModerationFilter(e.target.value)} className="field-input w-full sm:w-auto">
            <option value="">Любой статус</option>
            <option value="verified">Подтверждённые</option>
            <option value="unverified">На проверке</option>
            <option value="rejected">Отклонённые</option>
          </select>
          <Button type="submit" variant="primary" size={44}>Найти</Button>
        </div>
      </form>

      {loading ? (
        <div className="text-label-3 p-8" role="status">Загрузка...</div>
      ) : suppliers.length === 0 ? (
        <Card padding={false} className="p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
            <IconTruck className="w-10 h-10 text-[var(--accent)]" />
          </div>
          <h2 className="text-xl font-semibold text-label-1 mb-2">Поставщики не найдены</h2>
          <p className="text-label-3 text-sm">Создайте заявку — система автоматически найдёт поставщиков в радиусе объекта.</p>
        </Card>
      ) : (
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suppliers.map((s: any) => {
            const mod = MODERATION_LABELS[s.moderation_status || "unverified"];
            return (
              <li key={s.id} className="surface-card p-5 hover:shadow-small transition-shadow duration-150 ease-kimi-out">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-label-1 min-w-0">{s.name}</h3>
                  <Badge tone={mod.tone} className="shrink-0">{mod.text}</Badge>
                </div>
                <p className="text-sm text-label-2 mt-1">{s.city || s.email}</p>
                <p className="text-xs text-label-4 mt-1">{s.phone} | {s.email}</p>
                {isStaff && (
                  <div className="mt-3 flex gap-2 flex-wrap">
                    {s.moderation_status !== "verified" && (
                      <Button size={26} variant="primary" onClick={() => moderate(s.id, "verified")}>Подтвердить</Button>
                    )}
                    {s.moderation_status !== "rejected" && (
                      <Button size={26} variant="secondary" danger onClick={() => moderate(s.id, "rejected")}>Отклонить</Button>
                    )}
                    {s.moderation_status !== "unverified" && (
                      <Button size={26} variant="outline" onClick={() => moderate(s.id, "unverified")}>На проверку</Button>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
