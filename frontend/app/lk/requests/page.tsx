"use client";

import { useEffect, useState } from "react";
import { getRequests } from "@/lib/api";

export default function RequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRequests()
      .then((data) => setRequests(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-500">Zagruzka zayavok...</div>;
  }

  if (requests.length === 0) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Net zayavok</h2>
        <p className="text-gray-500 mb-6">Sozdayte pervuyu zayavku na pokupku materialov.</p>
        <a
          href="/lk/requests/new"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          + Novaya zayavka
        </a>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Moi zayavki</h1>
        <a
          href="/lk/requests/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
        >
          + Novaya
        </a>
      </div>
      <div className="space-y-4">
        {requests.map((req: any) => (
          <a
            key={req.id}
            href={}
            className="block bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition"
          >
            <div className="flex justify-between items-center">
              <div>
                <span className="font-mono font-bold text-blue-600">RFQ-{req.code}</span>
                <span className="ml-3 text-sm text-gray-500">
                  {new Date(req.created_at).toLocaleDateString("ru-RU")}
                </span>
              </div>
              <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                {req.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">{req.raw_text}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
