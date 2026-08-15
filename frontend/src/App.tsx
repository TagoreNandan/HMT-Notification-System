import { useEffect, useState } from "react";

type Product = {
  id: number;
  title: string;
  url: string;
  in_stock: boolean;
};

export default function App() {
  const [catalog, setCatalog] = useState<Product[]>([]);
  const [watchlist, setWatchlist] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState<number | null>(null);

  useEffect(() => {
    loadCatalog();
    loadWatchlist();
  }, []);

  async function loadCatalog() {
    const res = await fetch("http://127.0.0.1:8000/catalog");
    setCatalog(await res.json());
  }

  async function loadWatchlist() {
    const res = await fetch("http://127.0.0.1:8000/watchlist");
    const data = await res.json();
    setWatchlist(data.map((p: Product) => p.id));
  }

  async function toggle(product: Product) {
  setLoading(product.id);

  try {
    if (watchlist.includes(product.id)) {
      await fetch(`http://127.0.0.1:8000/watchlist/${product.id}`, {
        method: "DELETE",
      });

      setWatchlist((prev) => prev.filter((id) => id !== product.id));
    } else {
      await fetch(`http://127.0.0.1:8000/watchlist/${product.id}`, {
        method: "POST",
      });

      setWatchlist((prev) => [...prev, product.id]);
    }
  } catch (err) {
    console.error(err);
    alert("Something went wrong.");
  } finally {
    setLoading(null);
  }
}

  const filtered = catalog
  .filter((product) =>
    product.title.toLowerCase().includes(search.toLowerCase())
  )
  .sort((a, b) => {
    const aw = watchlist.includes(a.id);
    const bw = watchlist.includes(b.id);

    // watched first
    if (aw !== bw) return aw ? -1 : 1;

    // then out-of-stock first
    if (a.in_stock !== b.in_stock) {
      return Number(a.in_stock) - Number(b.in_stock);
    }

    // finally alphabetical
    return a.title.localeCompare(b.title);
  });

  return (
    <div
      style={{
        background: "#111827",
        minHeight: "100vh",
        color: "white",
        padding: 40,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
        }}
      >
        <h1
          style={{
            fontSize: 48,
            marginBottom: 10,
          }}
        >
          ⌚ HMT Watch Monitor
        </h1>

        <p
          style={{
            color: "#9ca3af",
            marginBottom: 30,
          }}
        >
          Get notified instantly when your favorite HMT watches are back in
          stock.
        </p>

        <input
          type="text"
          placeholder="Search watches..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%",
            padding: 14,
            borderRadius: 10,
            border: "1px solid #374151",
            background: "#1f2937",
            color: "white",
            fontSize: 16,
            marginBottom: 20,
            boxSizing: "border-box",
          }}
        />

        <p
          style={{
            color: "#9ca3af",
            marginBottom: 20,
          }}
        >
          Showing <strong>{filtered.length}</strong> watches • Watching{" "}
          <strong>{watchlist.length}</strong>
        </p>

        {filtered.map((product) => (
  <div
    key={product.id}
    style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      background: "#1f2937",
      padding: 20,
      marginBottom: 16,
      borderRadius: 12,
      border: watchlist.includes(product.id)
        ? "2px solid #16a34a"
        : "1px solid #374151",
    }}
  >
    <div>
      <a
        href={product.url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          fontSize: 20,
          fontWeight: 700,
          marginBottom: 10,
          color: "white",
          textDecoration: "none",
          display: "inline-block",
        }}
      >
        {product.title} ↗
      </a>

      <br />

      <span
        style={{
          display: "inline-block",
          padding: "6px 12px",
          borderRadius: 20,
          background: product.in_stock ? "#166534" : "#991b1b",
          color: "white",
          fontWeight: 600,
          fontSize: 14,
        }}
      >
        {product.in_stock ? "🟢 In Stock" : "🔴 Out of Stock"}
      </span>
    </div>

    <button
      disabled={loading === product.id}
      onClick={() => toggle(product)}
      style={{
        background: watchlist.includes(product.id)
          ? "#16a34a"
          : "#2563eb",
        color: "white",
        border: "none",
        padding: "12px 20px",
        borderRadius: 8,
        cursor: loading === product.id ? "not-allowed" : "pointer",
        opacity: loading === product.id ? 0.7 : 1,
        fontWeight: 600,
        fontSize: 15,
        minWidth: 120,
      }}
    >
      {loading === product.id
        ? "Updating..."
        : watchlist.includes(product.id)
        ? "✓ Watching"
        : "Notify Me"}
    </button>
  </div>
))}
          </div>
        ))
      </div>
  );
}