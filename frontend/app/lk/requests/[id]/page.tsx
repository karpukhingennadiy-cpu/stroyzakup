"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getRequest, parseRequest } from "@/lib/api";

export default function RequestDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [request, setRequest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);

  const load = () => {
    getRequest(id).then(setRequest).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleParse = async () => {
    setParsing(true);
    try {
      await parseRequest(id);
      load();
    } catch (err) {
      console.error(err);
    } finally {
      setParsing(false);
    }
  };

  if (loading) return <div className="text-gray-500">Zagruzka...</div>;
  if (!request) return <div className="text-red-500">Zayavka ne naydena</div>;

  return (
    <div className="max-w-3xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Zayavka <span className="font-mono text-blue-600">RFQ-{request.code}</span>
        </h1>
        <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
          {request.status}
        </span>
      </div>

      {/* Raw text */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <h2 className="text-sm font-semibold text-gray-500 mb-2">Iskhodnyy tekst</h2>
        <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{request.raw_text}</pre>
      </div>

      {/* Parse button */}
      {request.status === "draft" && (
        <button
          onClick={handleParse}
          disabled={parsing}
          className="mb-6 px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition disabled:opacity-50"
        >
          {parsing ? "Raspoznayom..." : "Raspoznat materialy (AI)"}
        </button>
      )}

      {/* Items */}
      {request.items && request.items.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-700">
              Pozitsii ({request.items.length})
            </h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <th className="text-left px-4 py-2">Material</th>
                <th className="text-left px-4 py-2">Kategoriya</th>
                <th className="text-right px-4 py-2">Kolichestvo</th>
                <th className="text-center px-4 py-2">Uverennost</th>
              </tr>
            </thead>
            <tbody>
              {request.items.map((item: any) => (
                <tr key={item.id} className="border-t border-gray-100">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800">{item.name}</div>
                    {item.brand && <div className="text-xs text-gray-400">{item.brand}</div>}
                    {item.spec && <div className="text-xs text-gray-400">{item.spec}</div>}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{item.category_name || "—"}</td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {item.quantity} {item.unit_name}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={}
                    >
                      {Math.round(item.confidence * 100)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
