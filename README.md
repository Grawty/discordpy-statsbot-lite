# Discord İstatistik Botu (StatsBot Lite)

YouTube istatistiklerini (abone, izlenme, son video) ve sunucu üye sayısını ses kanalında ve bot durumunda (presence) gösteren hafif Discord botu.

## Özellikler

- **Asenkron Altyapı:** `aiohttp` ile asenkron istekler (bot donmaz veya gateway kopmaları yaşamaz).
- **Optimize YouTube API:** `search` yerine kanalın `Uploads` oynatma listesi kullanılır, kota tüketimi %99 düşürülmüştür.
- **Ratelimit Koruması:** Abone sayısı değişmediği sürece kanal adı düzenleme isteği atılmaz.
- **Döngüsel Durum (Presence):** Belirlenen aralıklarla üye sayısı, YouTube izlenmesi, abone sayısı ve son video başlığı sırayla gösterilir.

## Kurulum

1. Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

2. `.env.example` dosyasını `.env` olarak kopyalayın ve bilgilerinizi girin:

```bash
cp .env.example .env
```

3. Botu başlatın:

```bash
python main.py
```
*(veya `python bot.py`)*

## Yapılandırma Seçenekleri (.env)

- `TOKEN`: Discord Bot Token
- `VOICE_CHANNEL_ID`: İstatistiğin yazılacağı ses kanalı ID'si
- `YOUTUBE_API_KEY`: YouTube Data API v3 anahtarı
- `YOUTUBE_CHANNEL_ID`: Takip edilecek YouTube kanalının ID'si
- `CHANNEL_UPDATE_INTERVAL`: Kanal adının güncellenme aralığı (saniye, min 300)
- `PRESENCE_INTERVAL`: Durum mesajının geçiş süresi (saniye, min 15)
- `STATS_CACHE_TTL`: YouTube verisinin önbellek süresi (saniye)
- `COMPACT_NUMBERS`: Sayıları `1.5M`, `12.5K` şeklinde gösterme (`true`/`false`)
- `VOICE_CONNECT`: Botun ses kanalına katılıp kalması (`true`/`false`)
- `VOICE_CHANNEL_TEMPLATE`: Kanal adı şablonu (Örn: `YouTube: {subscribers} ♥`)

## Lisans

[MIT](LICENSE)
