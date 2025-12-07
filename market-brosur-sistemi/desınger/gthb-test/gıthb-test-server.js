import express from "express";
import cors from "cors";
import bodyParser from "body-parser";
import fetch from "node-fetch"; // node-fetch v3 (ESM)

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(express.static("."));

// Yardımcı: metin içinden ilk JSON nesnesini çekmeye çalışır
function extractFirstJson(text) {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start >= 0 && end > start) {
    const candidate = text.slice(start, end + 1);
    try {
      return JSON.parse(candidate);
    } catch (e) {
      return null;
    }
  }
  return null;
}

// Deterministik fallback (OpenAI yoksa dönecek yapı)
function fallbackLayoutFromBody(body) {
  const page = body.page || { canvas: { width: 595, height: 842 }, objects: [] };
  const products = body.products || [];
  const templateExists = !!body.masterTemplate;
  const bg = (body.companyProfile && body.companyProfile.primaryColor) || "#ffffff";

  const baseX = 40;
  const baseY = 140;
  const gapX = 180;
  const gapY = 220;
  const baseImgW = 140;

  const productsLayout = (page.objects || []).map((o, idx) => {
    const row = Math.floor(idx / 3);
    const col = idx % 3;
    const sizeW = baseImgW * (o.scaleX || 1);
    const sizeH = Math.round(sizeW * 1.2);
    const product = products.find(p => p.id === o.productId) || {};
    return {
      productId: o.productId,
      position: { x: baseX + col * gapX, y: baseY + row * gapY },
      size: { width: sizeW, height: sizeH },
      role: idx === 0 ? "hero" : "secondary",
      priceFontSize: idx === 0 ? 22 : 16,
      nameFontSize: idx === 0 ? 14 : 12,
      price: product.price != null ? product.price : null,
      title: product.name || null,
      caption: product.caption || null
    };
  });

  return {
    model: "fallback",
    background: { color: bg, soften: true, backgroundPrompt: "Soft gradient using company primary color and subtle product-related textures" },
    template: {
      useMasterTemplate: templateExists,
      keepLogo: !!(body.companyProfile && body.companyProfile.logoUrl),
      headerBar: templateExists ? { height: 44, color: (body.masterTemplate && body.masterTemplate.styleProfile && body.masterTemplate.styleProfile.primaryColor) || "#111" } : null,
      footerBar: { height: 36, color: "#f3f4f6" }
    },
    products: productsLayout,
    annotations: { analysis: {}, globalAdvice: "deterministic fallback layout used (no OpenAI key)" },
    notes: "fallback layout (no OpenAI key)"
  };
}

// OpenAI için mesaj yapısını oluşturur (daha zengin prompt)
function buildOpenAiMessages(body) {
  const company = body.companyProfile || {};
  const masterTemplate = body.masterTemplate || null;
  const page = body.page || { canvas: { width: 595, height: 842 }, objects: [] };
  const products = body.products || [];

  const system = `
You are a professional brochure layout engineer and visual designer. You will produce two things:
1) A structured JSON describing precise layout placement, sizes, font sizes, and roles for each product on the given page.
2) A clear natural-language "backgroundPrompt" describing how the brochure background should be created (colors, gradients, textures, illustrative motifs), so a rendering engine or designer can produce the backdrop image.

REQUIREMENTS:
- Output ONLY valid JSON (no extra commentary). The JSON must conform to the schema described in the user message.
- Use absolute pixel coordinates relative to page.canvas.
- Use realistic visual decisions: hero product(s) larger, price font emphasis, consistent spacing.
- When company profile or masterTemplate is provided, include logo placement, header/footer bars, and use company colors in the backgroundPrompt.
- Include for each product detailed fields: productId, position {x,y}, size {width,height}, role, nameFontSize, priceFontSize, price, title (full), caption (short badge), and optional visualNotes (e.g., 'outline', 'dropShadow').
- Add a top-level field 'background' with { color, soften, backgroundPrompt }.
`;

  const user = {
    instruction: "Produce the JSON layout and background prompt for brochure generation.",
    companyProfile: company,
    masterTemplate: masterTemplate,
    page: page,
    products: products
  };

  return [
    { role: "system", content: system },
    { role: "user", content: "DATA:\n" + JSON.stringify(user, null, 2) }
  ];
}

app.post("/api/ai/layout", async (req, res) => {
  const body = req.body || {};
  const OPENAI_KEY = process.env.OPENAI_API_KEY;

  if (!OPENAI_KEY) {
    const fallback = fallbackLayoutFromBody(body);
    return res.json(fallback);
  }

  const messages = buildOpenAiMessages(body);

  try {
    const payload = {
      model: "gpt-4",
      messages,
      temperature: 0.2,
      max_tokens: 1200
    };

    const resp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENAI_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error("OpenAI error:", resp.status, text);
      const fallback = fallbackLayoutFromBody(body);
      fallback.notes = `openai_error_status_${resp.status}`;
      fallback.raw = text;
      return res.status(200).json(fallback);
    }

    const data = await resp.json();
    const assistant = data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
    if (!assistant) {
      const fallback = fallbackLayoutFromBody(body);
      fallback.notes = "openai_no_content";
      return res.json(fallback);
    }

    let parsed = null;
    try {
      parsed = JSON.parse(assistant);
    } catch (e) {
      parsed = extractFirstJson(assistant);
    }

    if (!parsed) {
      const fallback = fallbackLayoutFromBody(body);
      fallback.notes = "openai_parse_failed";
      fallback.raw = assistant;
      return res.json(fallback);
    }

    return res.json(parsed);
  } catch (err) {
    console.error("Server AI error:", err);
    const fallback = fallbackLayoutFromBody(body);
    fallback.notes = "server_exception";
    return res.json(fallback);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log("Broşür stüdyo server running on http://localhost:" + PORT);
  if (!process.env.OPENAI_API_KEY) {
    console.log("OPENAI_API_KEY not set → running in fallback (deterministic) mode.");
  }
});