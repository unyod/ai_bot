# Telegram AI Bot

Telegram uchun Python bot: matnli AI suhbat, suhbat xotirasi, ovozli xabar transkripsiyasi, rasm tahlili, PDF/DOCX xulosasi, admin boshqaruvi, Telegram Stars orqali premium obuna va webhook bilan production ishga tushirish.

## Imkoniyatlar

- `/start` va `/new`; xabarlar PostgreSQL’da saqlanadi va oxirgi `MAX_CONTEXT_MESSAGES` modeli konteksti sifatida yuboriladi.
- Ovozli xabarlar Whisper orqali matnga o‘giriladi, foydalanuvchiga transkripsiya ko‘rsatiladi va AI javob qaytaradi.
- Rasmlar AI Vision modeli bilan tahlil qilinadi; caption savol sifatida olinadi.
- PDF va DOCX matni ajratiladi; caption bo‘lsa so‘rov sifatida ishlatiladi.
- `/admin`, `/stats`, `/block`, `/unblock`, `/broadcast`; adminlar `.env` dagi `ADMIN_IDS` dan yuklanadi.
- `/premium` Telegram Stars (`XTR`) invoysini yuboradi. Muvaffaqiyatli to‘lov takror qayta ishlanmaydi va obuna uzaytiriladi.
- `USE_WEBHOOK=true` bo‘lsa Telegram yangilanishlari `POST /webhook` orqali keladi. Secret header tekshiriladi.

## Xavfsizlik

Hech qachon `BOT_TOKEN`, `OPENAI_API_KEY`, `WEBHOOK_SECRET` yoki DB parolini Git’ga va chatga joylamang. `.env` `.gitignore`da. Agar API kalit tasodifan chat yoki repoga tushib qolgan bo‘lsa, OpenAI Platform’da uni darhol revoke qiling.

## Lokal ishga tushirish (Docker)

1. `.env.example` dan `.env` nusxa oling va qiymatlarni faqat kompyuteringizda kiriting:

   ```bash
   cp .env.example .env
   ```

2. Lokal polling uchun `.env` ichida `ENVIRONMENT=development` va `USE_WEBHOOK=false` qoldiring.

3. Konteynerlarni ishga tushiring:

   ```bash
   docker compose up --build
   ```

4. Holatni tekshiring: `http://localhost:8000/health`.

`DATABASE_URL` ichidagi `db` host nomi Docker Compose uchun. Docker’siz ishga tushirishda uni `localhost` ga o‘zgartiring va PostgreSQL’ni alohida ishga tushiring.

## Docker’siz lokal ishga tushirish

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Development muhitida jadvallar avtomatik yaratiladi. Production’da Alembic ishlatiladi:

```bash
alembic upgrade head
```

## VPS, domen va HTTPS

1. Domeningizning `A` rekordini VPS IP manziliga yo‘naltiring.
2. `.env` da quyidagilarni kiriting:

   ```dotenv
   ENVIRONMENT=production
   USE_WEBHOOK=true
   WEBHOOK_URL=https://your-domain.example
   WEBHOOK_SECRET=long-random-secret
   DOMAIN=your-domain.example
   CERTBOT_EMAIL=you@example.com
   ```

3. VPS’da birinchi sertifikatni oling:

   ```bash
   chmod +x scripts/init-letsencrypt.sh
   ./scripts/init-letsencrypt.sh
   ```

4. To‘liq production stackni ishga tushiring:

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. `https://your-domain.example/health` endpointi `{"status":"ok","webhook":true}` qaytarishini tekshiring.

Nginx faqat `/health` va `/webhook` yo‘llarini ochadi. Certbot konteyneri sertifikatni har 12 soatda yangilashga harakat qiladi.

## Telegram Stars

`.env` dagi qiymatlarni sozlang:

```dotenv
PREMIUM_PRICE_STARS=100
PREMIUM_DURATION_DAYS=30
```

Telegram Stars uchun `provider_token` kerak emas va valyuta `XTR` bo‘ladi. Production’ga chiqishdan oldin @BotFather’da to‘lov funksiyasi yoqilganini tekshiring.

## Loyiha tuzilmasi

```text
app/
  database/     SQLAlchemy modellar, session va CRUD
  handlers/     Telegram komandalar va xabar turlari
  services/     OpenAI, xotira, to‘lov, hujjat servislar
  main.py       FastAPI, polling/webhook lifecycle
migrations/     Alembic migratsiyasi
nginx/          HTTPS reverse-proxy shabloni
scripts/        Birinchi Let’s Encrypt sertifikati uchun skript
```

