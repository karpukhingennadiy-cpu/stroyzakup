"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { IconHardHat } from "@/components/icons";
import { Button, Field, Card } from "@/components/ui";

interface QuoteItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  brand: string;
  spec: string;
}

interface ExistingQuote {
  id: number;
  status: string;
  delivery_cost: number | null;
  delivery_time: string;
  payment_terms: string;
  comment: string;
  items: {
    request_item_id: number;
    price: number;
    is_analog: boolean;
    brand: string;
  }[];
}

interface QuoteData {
  request_code: string;
  supplier_name: string;
  delivery_address: string;
  items: QuoteItem[];
  existing_quote: ExistingQuote | null;
}

interface FormItem {
  request_item_id: number;
  price: string;
  is_analog: boolean;
  brand: string;
}

export default function QuotePage() {
  const params = useParams();
  const token = params.token as string;
  const [data, setData] = useState<QuoteData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const [formItems, setFormItems] = useState<FormItem[]>([]);
  const [deliveryCost, setDeliveryCost] = useState("");
  const [deliveryTime, setDeliveryTime] = useState("");
  const [paymentTerms, setPaymentTerms] = useState("");
  const [comment, setComment] = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(API + "/public/quote/" + token + "/");
        if (!res.ok) {
          if (res.status === 404) throw new Error("Ссылка недействительна или устарела");
          throw new Error("Ошибка загрузки данных");
        }
        const d: QuoteData = await res.json();
        setData(d);

        const items: FormItem[] = d.items.map((item) => {
          const existing = d.existing_quote?.items.find(
            (ei) => ei.request_item_id === item.id
          );
          return {
            request_item_id: item.id,
            price: existing ? String(existing.price) : "",
            is_analog: existing?.is_analog || false,
            brand: existing?.brand || item.brand || "",
          };
        });
        setFormItems(items);

        if (d.existing_quote) {
          setDeliveryCost(d.existing_quote.delivery_cost != null ? String(d.existing_quote.delivery_cost) : "");
          setDeliveryTime(d.existing_quote.delivery_time || "");
          setPaymentTerms(d.existing_quote.payment_terms || "");
          setComment(d.existing_quote.comment || "");
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token, API]);

  const updateItem = (idx: number, field: keyof FormItem, value: any) => {
    setFormItems((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    const body = {
      items: formItems.map((fi) => ({
        request_item_id: fi.request_item_id,
        price: parseFloat(fi.price) || 0,
        is_analog: fi.is_analog,
        brand: fi.brand,
      })),
      delivery_cost: deliveryCost ? parseFloat(deliveryCost) : null,
      delivery_time: deliveryTime,
      payment_terms: paymentTerms,
      comment: comment,
    };

    try {
      const res = await fetch(API + "/public/quote/" + token + "/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || "Ошибка отправки");
      }
      setSuccess(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const shell = (children: React.ReactNode) => (
    <div className="min-h-screen bg-surface-ground py-6 sm:py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <header className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-[var(--radius-md)] bg-brand-sidebar flex items-center justify-center shrink-0">
            <IconHardHat className="w-5 h-5 text-brand" />
          </div>
          <span className="font-semibold text-label-1">Минитендер</span>
        </header>
        {children}
      </div>
    </div>
  );

  if (loading) {
    return shell(<p className="text-label-3 text-base" role="status">Загрузка заявки...</p>);
  }

  if (error && !data) {
    return shell(
      <Card>
        <h1 className="text-xl font-semibold text-label-1 mb-2">Ошибка</h1>
        <p className="text-[var(--danger)]" role="alert">{error}</p>
        <p className="text-label-3 text-sm mt-2">Проверьте ссылку или обратитесь к отправителю.</p>
      </Card>
    );
  }

  if (success) {
    return shell(
      <Card className="text-center p-10">
        <h1 className="text-xl font-semibold text-label-1 mb-2">Коммерческое предложение отправлено!</h1>
        <p className="text-label-2">Спасибо! Ваше КП по заявке <strong className="text-label-1">RFQ-{data?.request_code}</strong> принято.</p>
        <p className="text-label-3 text-sm mt-1">Мы свяжемся с вами при необходимости.</p>
      </Card>
    );
  }

  return shell(
    <>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-label-1">Запрос КП: RFQ-{data?.request_code}</h1>
        <p className="text-label-3 text-sm mt-1">
          <strong className="text-label-2 font-medium">Поставщик:</strong> {data?.supplier_name}
        </p>
        {data?.delivery_address && (
          <p className="text-label-3 text-sm">
            <strong className="text-label-2 font-medium">Адрес доставки:</strong> {data.delivery_address}
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <Card title="Позиции заявки" padding={false} className="mb-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="border-b border-separator text-left">
                  <th scope="col" className="px-6 py-3 text-xs font-medium text-label-3">Материал</th>
                  <th scope="col" className="px-3 py-3 text-xs font-medium text-label-3 text-right">Кол-во</th>
                  <th scope="col" className="px-3 py-3 text-xs font-medium text-label-3">Ед.</th>
                  <th scope="col" className="px-3 py-3 text-xs font-medium text-label-3">Цена за ед., руб</th>
                  <th scope="col" className="px-3 py-3 text-xs font-medium text-label-3 text-center">Аналог</th>
                  <th scope="col" className="px-6 py-3 text-xs font-medium text-label-3">Бренд</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((item, idx) => (
                  <tr key={item.id} className="border-b border-[var(--fill-1)]">
                    <td className="px-6 py-3">
                      <div className="font-medium text-label-1">{item.name}</div>
                      {item.spec && <div className="text-xs text-label-3 mt-0.5">{item.spec}</div>}
                    </td>
                    <td className="px-3 py-3 text-right text-label-1 tabular-nums">{item.quantity}</td>
                    <td className="px-3 py-3 text-label-3">{item.unit}</td>
                    <td className="px-3 py-3">
                      <label htmlFor={"price-" + item.id} className="sr-only">Цена за единицу: {item.name}</label>
                      <input
                        id={"price-" + item.id}
                        type="number" step="0.01" min="0" required
                        value={formItems[idx]?.price || ""}
                        onChange={(e) => updateItem(idx, "price", e.target.value)}
                        className="field-input w-28"
                        placeholder="0.00"
                      />
                    </td>
                    <td className="px-3 py-3 text-center">
                      <label htmlFor={"analog-" + item.id} className="sr-only">Предлагаю аналог: {item.name}</label>
                      <input
                        id={"analog-" + item.id}
                        type="checkbox"
                        checked={formItems[idx]?.is_analog || false}
                        onChange={(e) => updateItem(idx, "is_analog", e.target.checked)}
                        className="w-4 h-4 accent-[var(--accent)]"
                      />
                    </td>
                    <td className="px-6 py-3">
                      <label htmlFor={"brand-" + item.id} className="sr-only">Бренд: {item.name}</label>
                      <input
                        id={"brand-" + item.id}
                        type="text"
                        value={formItems[idx]?.brand || ""}
                        onChange={(e) => updateItem(idx, "brand", e.target.value)}
                        className="field-input w-32"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Условия поставки" className="mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field
              id="delivery-cost" label="Стоимость доставки, руб"
              type="number" step="0.01" min="0"
              value={deliveryCost} onChange={(e) => setDeliveryCost(e.target.value)}
            />
            <Field
              id="delivery-time" label="Срок поставки"
              type="text" placeholder="например: 5 рабочих дней"
              value={deliveryTime} onChange={(e) => setDeliveryTime(e.target.value)}
            />
            <Field
              id="payment-terms" label="Условия оплаты"
              type="text" placeholder="например: 100% постоплата"
              value={paymentTerms} onChange={(e) => setPaymentTerms(e.target.value)}
            />
            <div>
              <label htmlFor="quote-comment" className="block text-sm font-medium text-label-1 mb-1.5">Комментарий</label>
              <textarea
                id="quote-comment"
                value={comment} onChange={(e) => setComment(e.target.value)}
                className="field-input min-h-[60px] resize-y"
              />
            </div>
          </div>
        </Card>

        {error && (
          <p className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" variant="primary" size={44} loading={submitting}>
          {submitting ? "Отправка..." : "Отправить КП"}
        </Button>
      </form>
    </>
  );
}
