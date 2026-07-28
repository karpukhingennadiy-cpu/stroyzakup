"use client";

export default function HomePage() {
  return (
    <main style={{ fontFamily: "Inter, sans-serif", background: "#f8fafc", minHeight: "100vh" }}>
      <header style={{ padding: "80px 20px", textAlign: "center", background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)", color: "#fff" }}>
        <h1 style={{ fontSize: 48, fontWeight: 800, marginBottom: 16, letterSpacing: -1 }}>
          Минитендер<span style={{ color: "#f97316" }}>.рф</span>
        </h1>
        <p style={{ fontSize: 20, color: "#94a3b8", maxWidth: 600, margin: "0 auto 32px" }}>
          Платформа строительных закупок. Загрузите смету — AI найдёт поставщиков, сравнит цены, отправит RFQ.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <a href="/lk/requests/new" style={{ padding: "14px 32px", background: "#f97316", color: "#fff", borderRadius: 8, fontWeight: 600, textDecoration: "none", fontSize: 16 }}>
            Создать заявку
          </a>
          <a href="/lk" style={{ padding: "14px 32px", background: "rgba(255,255,255,0.1)", color: "#fff", borderRadius: 8, fontWeight: 600, textDecoration: "none", fontSize: 16 }}>
            Личный кабинет
          </a>
        </div>
      </header>
    </main>
  );
}
