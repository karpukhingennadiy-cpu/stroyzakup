"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createRequest } from "@/lib/api";

export default function NewRequestPage() {
  const router = useRouter();
  const [rawText, setRawText] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rawText.trim().length < 10) {
      setError("Minimum 10 simvolov");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const req = await createRequest(rawText.trim(), comment.trim());
      router.push();
    } catch (err: any) {
      setError(err.message || "Oshibka sozdaniya zayavki");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Novaya zayavka</h1>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Spisok materialov
          </label>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            required
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-y"
            placeholder={"Keramogranit seryy 600x600 - 150 m2
Plitochnyy kley KNAUF Fliesen - 100 meshkov
Dostavka: g. Podolsk"}
          />
          <p className="mt-1 text-xs text-gray-400">
            Ukazhite materialy, kolichestvo, gorod dostavki. AI avtomaticheski razberet spisok.
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Kommentariy (neobyazatelno)
          </label>
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={1000}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Osobye trebovaniya k materialam..."
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Sozdayom zayavku..." : "Sozdat zayavku"}
        </button>
      </form>
    </div>
  );
}
