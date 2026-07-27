"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

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
  }, [token]);

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

  if (loading) {
    return (
      <div style={{ maxWidth: 800, margin: "40px auto", padding: 20 }}>
        <p>Загрузка заявки...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ maxWidth: 800, margin: "40px auto", padding: 20 }}>
        <h2>Ошибка</h2>
        <p style={{ color: "red" }}>{error}</p>
        <p>Проверьте ссылку или обратитесь к отправителю.</p>
      </div>
    );
  }

  if (success) {
    return (
      <div style={{ maxWidth: 800, margin: "40px auto", padding: 20 }}>
        <h2>Коммерческое предложение отправлено!</h2>
        <p>Спасибо! Ваше КП по заявке <strong>RFQ-{data?.request_code}</strong> принято.</p>
        <p>Мы свяжемся с вами при необходимости.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: "20px auto", padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>Запрос КП: RFQ-{data?.request_code}</h1>
      <p><strong>Поставщик:</strong> {data?.supplier_name}</p>
      {data?.delivery_address && <p><strong>Адрес доставки:</strong> {data.delivery_address}</p>}

      <form onSubmit={handleSubmit}>
        <h3>Позиции заявки</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 20 }}>
          <thead>
            <tr style={{ background: "#f0f0f0", textAlign: "left" }}>
              <th style={{ padding: 8 }}>Материал</th>
              <th style={{ padding: 8 }}>Кол-во</th>
              <th style={{ padding: 8 }}>Ед.</th>
              <th style={{ padding: 8 }}>Цена за ед., руб</th>
              <th style={{ padding: 8 }}>Аналог</th>
              <th style={{ padding: 8 }}>Бренд</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item, idx) => (
              <tr key={item.id} style={{ borderBottom: "1px solid #ddd" }}>
                <td style={{ padding: 8 }}>
                  <div><strong>{item.name}</strong></div>
                  {item.spec && <div style={{ fontSize: 12, color: "#666" }}>{item.spec}</div>}
                </td>
                <td style={{ padding: 8 }}>{item.quantity}</td>
                <td style={{ padding: 8 }}>{item.unit}</td>
                <td style={{ padding: 8 }}>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={formItems[idx]?.price || ""}
                    onChange={(e) => updateItem(idx, "price", e.target.value)}
                    style={{ width: 100, padding: 4 }}
                    placeholder="0.00"
                  />
                </td>
                <td style={{ padding: 8, textAlign: "center" }}>
                  <input
                    type="checkbox"
                    checked={formItems[idx]?.is_analog || false}
                    onChange={(e) => updateItem(idx, "is_analog", e.target.checked)}
                  />
                </td>
                <td style={{ padding: 8 }}>
                  <input
                    type="text"
                    value={formItems[idx]?.brand || ""}
                    onChange={(e) => updateItem(idx, "brand", e.target.value)}
                    style={{ width: 120, padding: 4 }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <h3>Условия поставки</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
          <div>
            <label>Стоимость доставки, руб</label>
            <input type="number" step="0.01" min="0" value={deliveryCost}
              onChange={(e) => setDeliveryCost(e.target.value)}
              style={{ width: "100%", padding: 8, marginTop: 4 }} />
          </div>
          <div>
            <label>Срок поставки</label>
            <input type="text" value={deliveryTime}
              onChange={(e) => setDeliveryTime(e.target.value)}
              style={{ width: "100%", padding: 8, marginTop: 4 }}
              placeholder="например: 5 рабочих дней" />
          </div>
          <div>
            <label>Условия оплаты</label>
            <input type="text" value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value)}
              style={{ width: "100%", padding: 8, marginTop: 4 }}
              placeholder="например: 100% постоплата" />
          </div>
          <div>
            <label>Комментарий</label>
            <textarea value={comment}
              onChange={(e) => setComment(e.target.value)}
              style={{ width: "100%", padding: 8, marginTop: 4, minHeight: 60 }} />
          </div>
        </div>

        {error && <p style={{ color: "red", marginBottom: 12 }}>{error}</p>}

        <button type="submit" disabled={submitting}
          style={{
            padding: "12px 40px", fontSize: 16, background: "#0070f3", color: "#fff",
            border: "none", borderRadius: 6, cursor: submitting ? "not-allowed" : "pointer",
            opacity: submitting ? 0.7 : 1,
          }}>
          {submitting ? "Отправка..." : "Отправить КП"}
        </button>
      </form>
    </div>
  );
}
