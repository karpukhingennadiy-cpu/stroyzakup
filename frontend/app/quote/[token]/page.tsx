"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Send, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { ThemeToggle } from "@/components/theme";
import { IconHardHat } from "@/components/icons";

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

const inputClass =
  "w-full min-h-[60px] resize-y rounded-[var(--radius-md)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-3 py-2 text-sm text-[var(--label-primary)] shadow-[var(--shadow-input)] outline-none focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent)]/30";

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
          if (res.status === 404)
            throw new Error("Ссылка недействительна или устарела");
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
          setDeliveryCost(
            d.existing_quote.delivery_cost != null
              ? String(d.existing_quote.delivery_cost)
              : ""
          );
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
    <div className="min-h-screen bg-[var(--bg-ground)] py-6 sm:py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <header className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-[var(--radius-md)] bg-[var(--sidebar-bg)] flex items-center justify-center shrink-0 shadow-[var(--shadow-small)]">
            <IconHardHat className="w-5 h-5 text-[var(--accent)]" aria-hidden="true" />
          </div>
          <span className="font-semibold tracking-tight text-[var(--label-primary)]">
            Минитендер
          </span>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </header>
        {children}
      </div>
    </div>
  );

  if (loading) {
    return shell(
      <p className="text-[var(--label-tertiary)] text-base" role="status">
        Загрузка заявки...
      </p>
    );
  }

  if (error && !data) {
    return shell(
      <Card className="shadow-[var(--shadow-medium)]">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-6 h-6 text-[var(--danger)]" aria-hidden="true" />
            <h1 className="text-xl font-semibold tracking-tight text-[var(--label-primary)]">
              Ошибка
            </h1>
          </div>
          <p className="text-[var(--danger)]" role="alert">
            {error}
          </p>
          <p className="text-[var(--label-tertiary)] text-sm mt-2">
            Проверьте ссылку или обратитесь к отправителю.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (success) {
    return shell(
      <Card className="shadow-[var(--shadow-medium)]">
        <CardContent className="p-10 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--success-soft)] flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-[var(--success)]" aria-hidden="true" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-[var(--label-primary)] mb-2">
            Коммерческое предложение отправлено!
          </h1>
          <p className="text-[var(--label-secondary)]">
            Спасибо! Ваше КП по заявке{" "}
            <strong className="text-[var(--label-primary)]">
              RFQ-{data?.request_code}
            </strong>{" "}
            принято.
          </p>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            Мы свяжемся с вами при необходимости.
          </p>
        </CardContent>
      </Card>
    );
  }

  return shell(
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--label-primary)]">
          Запрос КП: RFQ-{data?.request_code}
        </h1>
        <p className="text-[var(--label-tertiary)] text-sm mt-1">
          <strong className="text-[var(--label-secondary)] font-medium">
            Поставщик:
          </strong>{" "}
          {data?.supplier_name}
        </p>
        {data?.delivery_address && (
          <p className="text-[var(--label-tertiary)] text-sm">
            <strong className="text-[var(--label-secondary)] font-medium">
              Адрес доставки:
            </strong>{" "}
            {data.delivery_address}
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="mb-6 overflow-hidden">
          <CardHeader>
            <CardTitle className="text-base">Позиции заявки</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Материал</TableHead>
                    <TableHead className="text-right">Кол-во</TableHead>
                    <TableHead>Ед.</TableHead>
                    <TableHead>Цена за ед., руб</TableHead>
                    <TableHead className="text-center">Аналог</TableHead>
                    <TableHead>Бренд</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((item, idx) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div className="font-medium text-[var(--label-primary)]">
                          {item.name}
                        </div>
                        {item.spec && (
                          <div className="text-xs text-[var(--label-tertiary)] mt-0.5">
                            {item.spec}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right text-[var(--label-primary)] tabular-nums">
                        {item.quantity}
                      </TableCell>
                      <TableCell className="text-[var(--label-tertiary)]">
                        {item.unit}
                      </TableCell>
                      <TableCell>
                        <Label htmlFor={`price-${item.id}`} className="sr-only">
                          Цена за единицу: {item.name}
                        </Label>
                        <Input
                          id={`price-${item.id}`}
                          type="number"
                          step="0.01"
                          min="0"
                          required
                          value={formItems[idx]?.price || ""}
                          onChange={(e) =>
                            updateItem(idx, "price", e.target.value)
                          }
                          className="w-28"
                          placeholder="0.00"
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Label htmlFor={`analog-${item.id}`} className="sr-only">
                          Предлагаю аналог: {item.name}
                        </Label>
                        <input
                          id={`analog-${item.id}`}
                          type="checkbox"
                          checked={formItems[idx]?.is_analog || false}
                          onChange={(e) =>
                            updateItem(idx, "is_analog", e.target.checked)
                          }
                          className="w-4 h-4 rounded border-[var(--separator)] accent-[var(--accent)]"
                        />
                      </TableCell>
                      <TableCell>
                        <Label htmlFor={`brand-${item.id}`} className="sr-only">
                          Бренд: {item.name}
                        </Label>
                        <Input
                          id={`brand-${item.id}`}
                          type="text"
                          value={formItems[idx]?.brand || ""}
                          onChange={(e) =>
                            updateItem(idx, "brand", e.target.value)
                          }
                          className="w-32"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Условия поставки</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="delivery-cost">
                  Стоимость доставки, руб
                </Label>
                <Input
                  id="delivery-cost"
                  type="number"
                  step="0.01"
                  min="0"
                  value={deliveryCost}
                  onChange={(e) => setDeliveryCost(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="delivery-time">Срок поставки</Label>
                <Input
                  id="delivery-time"
                  type="text"
                  placeholder="например: 5 рабочих дней"
                  value={deliveryTime}
                  onChange={(e) => setDeliveryTime(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="payment-terms">Условия оплаты</Label>
                <Input
                  id="payment-terms"
                  type="text"
                  placeholder="например: 100% постоплата"
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="quote-comment">Комментарий</Label>
                <textarea
                  id="quote-comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div
            className="mb-4 p-3 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-md)] text-sm"
            role="alert"
            aria-live="assertive"
          >
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={submitting}
          aria-busy={submitting}
          className="w-full sm:w-auto"
        >
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              Отправка...
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" aria-hidden="true" />
              Отправить КП
            </>
          )}
        </Button>
      </form>
    </>
  );
}