import { useState } from "react";
import { parseAndLogMessage } from "../services/api";

export default function MessageInput() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await parseAndLogMessage(text);
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h2 className="text-xl font-bold mb-4">✉️ Mesajdan İşlem Oluştur</h2>
      <textarea
        className="w-full h-32 p-3 border rounded resize-none"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="İşlem mesajını buraya yapıştır..."
      />
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Gönderiliyor..." : "Kaydet"}
      </button>

      {error && <p className="text-red-500 mt-2">{error}</p>}
      {result && (
        <div className="mt-4 p-4 border rounded bg-green-50">
          <p className="font-semibold">İşlem Oluşturuldu ✅</p>
          <pre className="text-sm mt-2">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
