# Path Deviation Tracker

Roboflow'un **Path Deviation** bloğundan esinlenen, NovaVision'a bağlanabilen yol
uyumluluk bileşeni. Bu paket görüntü tespiti yapmaz; Byte Tracker / tespit bloğundan
gelen `tracker_id`li sonuçların rotasını kontrol eder.

Her video ve `tracker_id` için nesnenin merkez noktaları saklanır. Bu gerçek rota,
referans rota ile **discrete Fréchet distance** kullanılarak karşılaştırılır. Küçük
sonuç, nesnenin beklenen yolu daha yakından takip ettiği anlamına gelir.

## Üretim davranışı

- Her `video_id` + `tracker_id` için rota ayrı tutulur; farklı videolar birbirine karışmaz.
- Zorunlu alanlar doğrulanır: `video_id`, `tracker_id`, merkez koordinatı ve en az iki
  noktadan oluşan referans rota.
- Her rotanın belleği varsayılan olarak en fazla 300 kare tutar; eski noktalar atılır.
- 1 saat yeni kare gelmeyen rota sıfırlanır. Bu değerler `PathDeviationSettings` ile
  değiştirilebilir.
- Çıktıdaki `path_deviation` piksel birimindedir. Eşik kararını iş akışı üstlenir;
  örneğin `path_deviation > 40` alarm olarak yorumlanabilir.

**Önemli:** `InMemoryPathStore` tek process içindir. Şirket ortamında birden fazla
worker/pod varsa, worker'ların hepsi aynı kalıcı `PathStore` uygulamasını (Redis gibi)
kullanmalıdır. Aksi halde iki ardışık kare farklı workerlara düştüğünde rota geçmişi
kaybolur. Canlı ortama almadan önce bu store adaptörü, kullandığınız Redis sözleşmesi
ile bağlanmalıdır.

## Girdi ve çıktı sözleşmesi

```python
executor.process(
    video_id="camera-12-2026-08-09T10:00",  # Capsule bunu inputImage metadata'sından alır.
    detections=[{"tracker_id": "vehicle-27", "x": 120.5, "y": 320.0}],
    reference_path=[[100, 320], [200, 320], [300, 320]],
)
```

Tespit merkezi `x`/`y` veya `left`/`top`/`width`/`height` olarak verilebilir. Her
girdi tespiti korunur; `metadata.path_deviation` ve `metadata.path_points` eklenmiş
biçimde döner.

## Yapı

- `src/models/PackageModel.py`: NovaVision Package Model şeması
- `src/utils/engine.py`: SDK'dan bağımsız, doğrulama ve durum yönetimli çekirdek
- `src/executors/PathDeviationTrackerExecutor.py`: NovaVision `Component` tabanlı capsule çalıştırıcısı
- `examples/run_example.py`: SDK gerektirmeyen, çalışır örnek

## Hızlı deneme

```bash
cd /Users/sena/Documents/Playground/path-deviation-tracker
python3 examples/run_example.py
```

Örnek üç ardışık kare gönderir. Aynı `video_id` ve `tracker_id` kullanıldığı için
rota korunur; üçüncü karedeki sonuç, o ana kadarki rotanın referans yoldan sapmasıdır.

## NovaVision girdileri

Capsule executor şu parametreleri bekler:

- `inputImage`: Video Feed'den gelen `Image`; `video_metadata.video_identifier` içermelidir
- `detections`: Object Tracking'den gelen `Detections`; her tespitte `tracker_id` bulunmalıdır
- `referencePath`: En az iki `[x, y]` noktası
- `triggeringAnchor`: `CENTER`, `TOP_CENTER` veya `BOTTOM_CENTER`

Çıktıda her detection'ın `metadata.path_deviation` alanı eklenir. Durum bellek içindedir; bu yüzden
ardışık video kareleri aynı çalışan süreçte işlenmelidir.

### Flow bağlantıları

- Video Feed `Image` → Path Deviation `Image` (`inputImage`)
- Object Tracking `Detections` → Path Deviation `Detections` (`detections`)
- Path Deviation `Detections/ROI` (`outputDetections`) → Draw Bounding Box `Detections/ROI`
- Video Feed `Image` → Draw Bounding Box `Image`
