import express from "express";
import cors from "cors";
import bodyParser from "body-parser";

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(".")); // index.html, js, css

// Basit sahte AI layout: ürünleri 3xN grid'e dizer
app.post("/api/ai/layout", async (req, res) => {
  const { page } = req.body;
  try {
    const baseX = 40;
    const baseY = 160;
    const gapX = 180;
    const gapY = 220;

    const layout = {
      background: { color: "#f9fafb" },
      products: (page.objects || []).map((o, idx) => {
        const row = Math.floor(idx / 3);
        const col = idx % 3;
        return {
          productId: o.productId,
          position: { x: baseX + col * gapX, y: baseY + row * gapY },
          size: { width: 160, height: 220 },
          role: idx === 0 ? "hero" : "secondary"
        };
      })
    };

    res.json(layout);
  } catch (err) {
    console.error(err);
    res.status(500).send("AI layout error");
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log("Broşür stüdyo server running on http://localhost:" + PORT);
});
