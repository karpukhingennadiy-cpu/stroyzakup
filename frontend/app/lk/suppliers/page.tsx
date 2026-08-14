"use client";

import { useEffect, useState } from "react";
import { getSuppliers, getMe, api } from "@/lib/api";
import { CheckCircle2, X, RotateCcw } from "lucide-react";
import { IconTruck, IconSearch, IconPlus } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

const MODERATION_LABELS: Record<string, { text: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  verified: { text: "Подтверждён", variant: "default" },
  unverified: { text: "На проверке", variant: "secondary" },
  rejected: { text: "Отклонён", variant: "destructive" },
};

const selectClass =
  "h-9 rounded-[var(--radius-md)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-3 text-sm text-[var(--label-primary)] shadow-[var(--shadow-input)] outline-none focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent)]/30";

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
  const [addForm, setAddForm] = useState({
    name: "",
    email: "",
    phone: "",
    site: "",
    city: "",
    address: "",
    supplier_type: "unknown",
  });
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
    api("/suppliers/categories/")
      .then((data) => setCategories(data.results || data))
      .catch(() => {});
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (city) params.city = city;
    if (moderationFilter) params.moderation_status = moderationFilter;
    load(params);
  };

  const moderate = async (id: number, status: string) => {
    try {
      await api("/suppliers/" + id + "/moderate/", {
        method: "POST",
        body: JSON.stringify({ status }),
      });
      setSuppliers(
        suppliers.map((s) =>
          s.id === id ? { ...s, moderation_status: status } : s
        )
      );
      setNotice(
        status === "verified"
          ? "Поставщик подтверждён"
          : status === "rejected"
          ? "Поставщик отклонён — исключён из подбора"
          : "Статус обновлён"
      );
      setTimeout(() => setNotice(""), 4000);
    } catch (e: any) {
      setNotice("Ошибка модерации: " + e.message);
    }
  };

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
      setAddForm({
        name: "",
        email: "",
        phone: "",
        site: "",
        city: "",
        address: "",
        supplier_type: "unknown",
      });
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
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--label-primary)]">
            Поставщики
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            База проверенных поставщиков стройматериалов
          </p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <IconPlus className="w-4 h-4 mr-2" aria-hidden="true" />
          Добавить поставщика
        </Button>
      </div>

      {notice && (
        <div
          className="mb-4 p-3 bg-[var(--success-soft)] border border-[var(--separator)] text-[var(--success)] rounded-[var(--radius-lg)] text-sm"
          role="status"
          aria-live="polite"
        >
          {notice}
        </div>
      )}

      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Новый поставщик</CardTitle>
          </CardHeader>
          <CardContent>
            {addError && (
              <div
                className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm"
                role="alert"
              >
                {addError}
              </div>
            )}
            <form onSubmit={handleAdd} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sup-name">
                    Название <span className="text-[var(--danger)]">*</span>
                  </Label>
                  <Input
                    id="sup-name"
                    required
                    value={addForm.name}
                    onChange={(e) =>
                      setAddForm({ ...addForm, name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sup-email">Email</Label>
                  <Input
                    id="sup-email"
                    type="email"
                    value={addForm.email}
                    onChange={(e) =>
                      setAddForm({ ...addForm, email: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sup-phone">Телефон</Label>
                  <Input
                    id="sup-phone"
                    value={addForm.phone}
                    onChange={(e) =>
                      setAddForm({ ...addForm, phone: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sup-site">Сайт</Label>
                  <Input
                    id="sup-site"
                    placeholder="https://..."
                    value={addForm.site}
                    onChange={(e) =>
                      setAddForm({ ...addForm, site: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sup-address">Адрес</Label>
                  <Input
                    id="sup-address"
                    placeholder="Город, улица"
                    value={addForm.address}
                    onChange={(e) =>
                      setAddForm({ ...addForm, address: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sup-type">Тип</Label>
                  <select
                    id="sup-type"
                    value={addForm.supplier_type}
                    onChange={(e) =>
                      setAddForm({ ...addForm, supplier_type: e.target.value })
                    }
                    className={selectClass + " w-full"}
                  >
                    <option value="unknown">Неизвестно</option>
                    <option value="manufacturer">Производитель</option>
                    <option value="dealer">Дилер</option>
                  </select>
                </div>
              </div>
              {categories.length > 0 && (
                <fieldset>
                  <legend className="text-xs text-[var(--label-tertiary)] mb-2">
                    Категории материалов:
                  </legend>
                  <div className="flex flex-wrap gap-2">
                    {categories.map((c: any) => {
                      const active = selectedCats.has(c.id);
                      return (
                        <button
                          type="button"
                          key={c.id}
                          aria-pressed={active}
                          onClick={() => {
                            const next = new Set(selectedCats);
                            active ? next.delete(c.id) : next.add(c.id);
                            setSelectedCats(next);
                          }}
                          className={
                            "px-3 py-1.5 rounded-full text-xs font-medium border transition-colors " +
                            (active
                              ? "bg-[var(--label-primary)] text-[var(--bg-primary)] border-transparent"
                              : "bg-transparent text-[var(--label-secondary)] border-[var(--separator)] hover:bg-[var(--fill-1)]")
                          }
                        >
                          {c.name}
                        </button>
                      );
                    })}
                  </div>
                </fieldset>
              )}
              <div className="flex gap-3">
                <Button type="submit" disabled={!addForm.name.trim() || addLoading}>
                  {addLoading ? "Сохраняем..." : "Сохранить"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                >
                  Отмена
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSearch} className="mb-6" role="search">
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-3 flex-wrap items-end">
              <div className="flex-1 min-w-[200px] space-y-2">
                <Label htmlFor="supplier-search">Поиск</Label>
                <div className="relative">
                  <IconSearch
                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--label-quaternary)]"
                    aria-hidden="true"
                  />
                  <Input
                    id="supplier-search"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Поиск по названию..."
                    className="pl-9"
                  />
                </div>
              </div>
              <div className="w-full sm:w-40 space-y-2">
                <Label htmlFor="supplier-city">Город</Label>
                <Input
                  id="supplier-city"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Город"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="supplier-moderation">Статус</Label>
                <select
                  id="supplier-moderation"
                  value={moderationFilter}
                  onChange={(e) => setModerationFilter(e.target.value)}
                  className={selectClass + " w-full sm:w-auto"}
                >
                  <option value="">Любой статус</option>
                  <option value="verified">Подтверждённые</option>
                  <option value="unverified">На проверке</option>
                  <option value="rejected">Отклонённые</option>
                </select>
              </div>
              <Button type="submit">Найти</Button>
            </div>
          </CardContent>
        </Card>
      </form>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : suppliers.length === 0 ? (
        <Card>
          <CardContent className="p-16 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
              <IconTruck className="w-10 h-10 text-[var(--accent)]" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-[var(--label-primary)] mb-2">
              Поставщики не найдены
            </h2>
            <p className="text-[var(--label-tertiary)] text-sm">
              Создайте заявку — система автоматически найдёт поставщиков в радиусе объекта.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden shadow-[var(--shadow-xs)]">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead className="hidden sm:table-cell">Город</TableHead>
                  <TableHead className="hidden md:table-cell">Контакты</TableHead>
                  <TableHead>Статус</TableHead>
                  {isStaff && <TableHead className="text-right">Действия</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map((s: any) => {
                  const mod = MODERATION_LABELS[s.moderation_status || "unverified"];
                  return (
                    <TableRow key={s.id}>
                      <TableCell className="font-medium text-[var(--label-primary)]">
                        {s.name}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-[var(--label-tertiary)]">
                        {s.city || "—"}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-[var(--label-tertiary)]">
                        {s.phone && <div>{s.phone}</div>}
                        {s.email && <div>{s.email}</div>}
                      </TableCell>
                      <TableCell>
                        <Badge variant={mod.variant}>{mod.text}</Badge>
                      </TableCell>
                      {isStaff && (
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end flex-wrap">
                            {s.moderation_status !== "verified" && (
                              <Button
                                size="sm"
                                onClick={() => moderate(s.id, "verified")}
                              >
                                <CheckCircle2 className="w-3 h-3 mr-1" aria-hidden="true" />
                                Подтвердить
                              </Button>
                            )}
                            {s.moderation_status !== "rejected" && (
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => moderate(s.id, "rejected")}
                              >
                                <X className="w-3 h-3 mr-1" aria-hidden="true" />
                                Отклонить
                              </Button>
                            )}
                            {s.moderation_status !== "unverified" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => moderate(s.id, "unverified")}
                              >
                                <RotateCcw className="w-3 h-3 mr-1" aria-hidden="true" />
                                На проверку
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}