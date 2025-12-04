import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

prompt = """
Sen Apple, Stripe ve Linear'dan ilham alan minimalist UI/UX tasarımcısısın.

GÖREV: Market broşür oluşturucu için SADECE 2 BUTONLU, ultra-modern bir açılış ekranı tasarla.

KURALLAR:
1. SADECE 2 seçenek: "Hızlı Broşür" ve "Özel İstek"
2. Açık koyu tema (dark mode ama çok koyu değil, soft)
3. Subtle animasyonlar (abartısız)
4. Glassmorphism veya neumorphism kullan
5. AI/futuristik his olsun ama çocuksu değil, profesyonel

2 BUTONUN FONKSİYONLARI:
- "Hızlı Broşür": Yüklü ürünlerden anında broşür (1 tık)
- "Özel İstek": AI ile sohbet edip istediğini anlat

ÇIKTI (JSON formatında):
{
  "konsept_adi": "...",
  "tasarim_dili": "...",
  "renk_paleti": {
    "arka_plan": "#...",
    "kart_bg": "#...", 
    "vurgu_1": "#...",
    "vurgu_2": "#...",
    "metin": "#..."
  },
  "buton_1": {
    "baslik": "...",
    "alt_baslik": "...",
    "ikon": "emoji veya ikon önerisi",
    "hover_efekti": "..."
  },
  "buton_2": {
    "baslik": "...",
    "alt_baslik": "...", 
    "ikon": "emoji veya ikon önerisi",
    "hover_efekti": "..."
  },
  "animasyonlar": ["liste"],
  "merkez_eleman": "açılışta merkezdeki görsel/animasyon"
}

Minimalist ama etkileyici ol. Stripe.com veya linear.app kalitesinde düşün.
"""

response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': prompt}],
    max_tokens=2000
)

print(response.choices[0].message.content)

