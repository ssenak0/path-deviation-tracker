# Path Deviation Tracker

Bu paket, video akışındaki araç veya nesnelerin çizilen referans rotadan (şerit vb.) ne kadar saptığını takip eden bir NovaVision akış bileşenidir.

Nesne takibinden gelen koordinatları birleştirerek aracın izlediği yolu çıkarır ve bunu belirlediğimiz ideal hat ile karşılaştırır. İki rota arasındaki mesafeyi hesaplamak için Fréchet mesafesi algoritmasını kullanıyor.

## Nasıl Çalışıyor?

Modül gelen her görüntü karesindeki algılamaları tarar ve nesnelerin `tracker_id` bilgisine göre geçtiği noktaları bellekte toplar. Aracın çizdiği bu anlık rota ile referans rota arasındaki sapmayı ölçer.

Eğer hesaplanan sapma değeri belirlediğimiz eşiği geçerse, sistem uyarı verir ve nesne kutusunun rengini kırmızıya çevirir. Normal ilerleyen nesneler yeşil kutu ile gösterilir.

## Akış Motorunda Kullanımı

Bu modülün nesne takibi yapabilmesi için akış zincirinde kendisinden önce mutlaka bir takip modülü (örneğin ByteTrack) konulmalıdır.

Örnek bağlantı sırası şu şekildedir:
[Kamera Akışı] -> [YOLO Object Detection] -> [ByteTrack Object Tracker] -> [Path Deviation Tracker] -> [Video Çıkışı / Ekran]

## Arayüz Parametreleri

- **Triggering Anchor:** Nesne kutusunun neresinden takip yapılacağı ayarı. Araç takibi için yere basma noktasını veren `BOTTOM_CENTER` seçilmesi önerilir. Varsayılan değer `CENTER` olarak gelir.
- **Referans Rota Koordinatları:** İdeal şeridin veya hattın piksel bazındaki koordinat listesi. (Örn: `[[100, 200], [200, 300], [300, 400]]`)
- **Maksimum Fréchet Sapma Eşiği:** Sapma uyarısının tetiklenmesi için belirlenen limit mesafe değeri. Varsayılanı 50.0 pikseldir.
- **Rota ve BBox Görsellemesi:** Ekran üstünde rotaların ve algılama kutularının çizilip çizilmeme ayarı (`True` / `False`).

## Çıktı Yapısı

Modül iki farklı çıktı üretir:
1. `outputAnnotatedImage`: Üzerine rotaların ve kutuların çizildiği işlenmiş görsel.
2. `outputPathDeviation`: Algılanan nesnelerin listesi. Her nesnenin içinde şu bilgiler yer alır:
   - `tracker_id`: Nesne takip numarası
   - `path_deviation`: Hesaplanan Fréchet mesafe skoru
   - `is_deviated`: Sapma olup olmadığı (`True` / `False`)
   - `deviation_status`: Sapma varsa `ALERT_DEVIATED`, yoksa `ON_TRACK` durum bilgisi
