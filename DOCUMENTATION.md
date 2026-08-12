# PathDeviationTracker - DOCUMENTATION

## 1. Genel Bakış

### Paketin amacı ve ne yaptığı

PathDeviationTracker paketi, NovaVision platformunda nesne takibi (object tracking) yapılan video akışlarında, hareketli araçların önceden belirlenmiş bir referans rotasına olan dik sapma miktarını (path deviation) gerçek zamanlı hesaplayan uzamsal analiz (spatial analytics) kapsülüdür. Bu paket:

- Anlık kareleri ve tespit (detections) listelerini (single veya batch) kabul eder
- Otonom ölçekleme (auto-scaling) ile çizilen referans rotasını gerçek video çözünürlüğüne adapte eder
- Her bir aracın referans çizgisine (veya çokgenine) olan uzaklığını (piksel bazında) hesaplar
- Algoritma çıktılarında tespit listesini zenginleştirerek (enrichment) `metadata` içerisine `path_deviation` ve `debug_reference_path` verilerini ekler

### Temel özellikler

- ✅ Otonom Çözünürlük ve Ölçekleme (Auto-Scaling)
- ✅ Yüksek hızlı, doğrudan bellek içi (in-memory) I/O Bypass optimizasyonu
- ✅ Sıfır gecikme (zero-latency) ile uzamsal hesaplama
- ✅ Sınır kutusu çapa noktası (triggering anchor) yönetimi
- ✅ Gelişmiş arayüz çizimi (Polygon / Polyline) desteği
- ✅ Pydantic tabanlı model tanımları (girdi/çıktı/konfigürasyon)

### Desteklenen sınıflar / modeller / tipler
| ID | İsim | Açıklama |
|----|------|---------|
| 1  | `PathDeviationTrackerExecutor` | Capsulenin ana executor sınıfı — otonom ölçeklemeyi yönetir ve engine'i tetikler |
| 2  | `PackageModel` | Paket genel yapı tanımı (configs, executor vb.) |
| 3  | `InputImage` | Pydantic input modeli — oto-ölçekleme referansı için single veya list image |
| 4  | `InputDetections` | Pydantic input modeli — takip edilen araçların detection verileri |
| 5  | `OutputDetections` | Pydantic output modeli — zenginleştirilmiş detection verileri |
| 6  | `ConfigReferenceRoi` | Arayüz üzerinden çizilen Polygon/Polyline çizim verilerini tutan config |
| 7  | `ConfigTriggeringAnchor` | Sınır kutusunun neresinin hesaplama merkezi alınacağını tutan config |

---

## 2. Mimari ve Teknolojiler

### Teknoloji Stack'i
- Framework: Python 3.x
- Veri Yönetimi: Redis (NovaVision SDK üzerinden in-memory object taşıma)
- İşleme: Geometrik Matematik Algoritmaları, OpenCV (NovaVision Image formatı), NumPy
- SDK Bileşenleri: `sdks.novavision` (Capsule, Image, PackageHelper, Executor, Application)

### Her teknolojinin rolü ve kullanımı (kart formatında)

- Python 3.x
  - Rol: Ana programlama dili
  - Kullanım: Paket mantığı, Pydantic modeller, iş mantığı, geometrik mesafe formülleri

- Geometrik Hesaplamalar (engine.py)
  - Rol: Uzamsal analiz (Spatial analysis)
  - Kullanım: İki nokta/çokgen arası mesafe formülleri ve nokta-doğru uzaklığı tespiti

- OpenCV
  - Rol: Görüntü (Image) Modeli Formatı
  - Kullanım: NovaVision arayüzünden kapsüle gönderilen görüntülerin (inputImage) tipi ve formatının (OpenCV) standartlara uyumlu olması ve çözünürlük verisinin okunması

- json & json.loads
  - Rol: Otonom ölçekleme veri dönüşümü
  - Kullanım: Arayüzden gelen karmaşık String/JSON çizim verilerinin güvenli ayrıştırılması

- Pydantic
  - Rol: Input/Output/Config model validasyonu ve schema tanımı
  - Kullanım: `PackageModel.py` içerisindeki modeller, validasyon süreçleri

- sdks.novavision (SDK Bileşenleri)
  - Rol: Paket geliştirme için yardımı sınıflar (Capsule, Image, Request/Response modelleri, Executor, PackageHelper)
  - Kullanım: `Capsule` sınıfı ile executor çalışma mantığı, standart Pydantic tipleri (Image, Detection) entegrasyonu

### Proje yapısı (tree formatında)

```text
PathDeviationTracker/
├── LICENSE                              # Lisans bilgisi
├── README.md                            # Kısa proje açıklaması ve çalışma prensipleri
├── DOCUMENTATION.md                     # (Bu dosya) Otomatik üretilmiş detaylı dokümantasyon
├── setup.py                             # Paket kurulumu
├── src/
│   ├── __init__.py
│   ├── executors/
│   │   └── PathDeviationTrackerExecutor.py # Executor sınıfı: Otonom ölçekleme ve run çağrısı
│   ├── models/
│   │   └── PackageModel.py              # Pydantic modeller: Inputs, Outputs, Configs, Request, Response
│   └── utils/
│       ├── engine.py                    # Mesafe hesaplamaları ve trackerID bellek yönetimi
│       └── response.py                  # Response oluşturma helper'ı
```

Açıklamalar:
- `PathDeviationTrackerExecutor.py` — Kapsülün ana çalışma mantığını içeren executor. Otonom ölçekleme işlemlerini hesaplar, `engine.py` üzerinden uzamsal analizi gerçekleştirir ve `build_response()` ile sonucu paketler.
- `PackageModel.py` — Pydantic modeller: Input, Output, Config, Request, Response tanımları.
- `utils/engine.py` — `PathDeviationService` sınıfı üzerinden nesnelerin poligona veya çizgiye dik olan uzaklıklarını hesaplar.
- `utils/response.py` — executor context'inden çıkış modelini NovaVision formatında oluşturur.

---

## 3. Executor'lar ve Çalışma Modları

### `PathDeviationTrackerExecutor` (Tam path: `src/executors/PathDeviationTrackerExecutor.py`)

- Amaç:
  - Video Feed üzerinden videonun gerçek boyutlarını elde edip (Otonom Ölçekleme), araçların belirlenen referans rotasına olan dikey sapma mesafelerini bulmak ve `metadata` içerisine gömmek.

- Kullanım senaryosu:
  - ✅ Otonom şerit takibi ihlalleri
  - ✅ Sınır güvenliği ve yasaklı bölgeye (çizgiye) yaklaşma ihlalleri
  - ✅ Akıllı trafik kontrol ve izleme sistemleri

- İşleyiş (numaralı adımlar):
  1. `run()` çağrıldığında gelen `detections` (araç koordinatları) ve `inputImage` (gerçek boyut referansı) okunur.
  2. Kullanıcının arayüzden girdiği (ROI) json verisi ayrıştırılarak (json.loads) UI çizim alanı (Örn: 3420x1880) ile gerçek video boyutları (Örn: 1920x1080) arasındaki oranlar (`scale_x`, `scale_y`) hesaplanır.
  3. `PathDeviationService` tetiklenerek bu ölçeklendirilmiş noktalar ve çapa noktası (triggering anchor) üzerinden her aracın doğruya olan mesafesi (dik uzaklık) bulunur.
  4. Hesaplanan değer ve ölçeklendirilmiş referans çizgisi `metadata` objesinin altına kaydedilir.
  5. `build_response` ile zenginleştirilmiş Pydantic `Response` nesnesi oluşturulur.

- Python sınıfı (tam path): `capsules.PathDeviationTracker.src.executors.PathDeviationTrackerExecutor.PathDeviationTrackerExecutor`

- Temel metodlar:
  - `__init__(self, request, bootstrap)` : Executor başlatma, request -> PackageModel mapping
  - `_parse_reference_roi(self)`: String olarak gelen ROI verisini parçalayarak otonom ölçeklendirme çarpanlarını (scale) tespit eden metod.
  - `run(self)` : Otonom ölçekleme, engine üzerinden uzamsal hesaplama ve response oluşturma ana döngüsü.

---

## 4. Girdi (Input) Parametreleri

### 4.1 `InputImage` (Pydantic Model)
- Tanım: Tek bir image veya image listesi alabilen input. Burada oto-ölçekleme için salt okunur (read-only) referans olarak kullanılır.
- Kullanıldığı executor'lar:
  - PathDeviationTrackerExecutor: ✅

### 4.2 `InputDetections` (Pydantic Model)
- Tanım: ObjectTracking modülünden gelen ve takip edilen araçların güncel konumlarını, `trackerID`'lerini barındıran tespit listesi (Detections).
- Yapı örneği (JSON):
```json
{
  "name": "detections",
  "type": "list",
  "value": [
    {
      "boundingBox": {"left": 100, "top": 50, "width": 200, "height": 250},
      "confidence": 0.75,
      "classId": 2,
      "classLabel": "car",
      "trackerID": 1
    }
  ]
}
```
- Kullanıldığı executor'lar:
  - PathDeviationTrackerExecutor: ✅

---

## 5. Konfigürasyon (Config) Parametreleri

### 5.1 `ConfigReferenceRoi`
- Tanım: Sapmanın ölçüleceği referans rotasını belirten gelişmiş arayüz çizim aracıdır (Polygon veya Polyline). Koordinatlar otonom olarak ölçeklendirilir.
- Örnek kullanım (JSON):
```json
{
  "name": "referenceRoi",
  "value": "{\"config\": {\"canvasSize\": [3420, 1880]}, \"shapes\": [{\"points\": [[100, 200], [400, 500]]}]}",
  "type": "string",
  "field": "textarea"
}
```
- Kullanıldığı executor'lar:
  - PathDeviationTrackerExecutor: ✅

### 5.2 `ConfigTriggeringAnchor`
- Tanım: Sınır kutusunun (aracın) neresinin hesaplama merkezi alınacağını belirler (`CENTER`, `BOTTOM_CENTER`, `TOP_CENTER`).
- Örnek kullanım (JSON):
```json
{
  "name": "triggeringAnchor",
  "value": "BOTTOM_CENTER",
  "type": "string",
  "field": "dropdownlist"
}
```
- Kullanıldığı executor'lar:
  - PathDeviationTrackerExecutor: ✅

---

## 6. Çıktı (Output) Parametreleri

### 6.1 `OutputDetections` (Pydantic Model)
- Tanım: İçerisinde standart `Detection` yapısına ek olarak `metadata` altında uzamsal analiz (sapma) sonuçlarını bulunduran output container.
- Yapı örneği (JSON):
```json
{
  "name": "outputDetections",
  "type": "list",
  "value": [
    {
      "boundingBox": {
        "left": 1084.73,
        "top": 112.16,
        "width": 49.78,
        "height": 36.85
      },
      "confidence": 0.45,
      "classLabel": "car",
      "trackerID": 1,
      "metadata": {
        "path_deviation": 1001.02,
        "path_points": 1,
        "debug_reference_path": [
          [962.8, 112.59],
          [901.6, 950.17]
        ]
      }
    }
  ]
}
```
- Kullanıldığı executor'lar:
  - PathDeviationTrackerExecutor: ✅

---

## 7. Veri Modelleri

### PackageModel hiyerarşisi (ASCII tree)
```text
PackageModel (Package)
├── configs (PackageConfigs)
│   └── executor (ConfigExecutor)
│       └── value (PathDeviationTrackerExecutor)
│           └── value (PathDeviationRequest or Response)
│               ├── inputs (PathDeviationInputs) -> inputImage, detections
│               ├── configs (PathDeviationConfigs) -> [referenceRoi, triggeringAnchor]
│               └── outputs (PathDeviationOutputs) -> outputDetections
```

### Request / Response akışları (her executor için)

- PathDeviationTrackerExecutor (ASCII sequence):
```text
[Client/Pipeline] ----JSON Request containing-> [PackageModel (configs->executor->value->PathDeviationRequest)]
      |
      V
[Executor: PathDeviationTrackerExecutor] --run()
      |
      V
1. inputImage'den videonun gerçek çözünürlüğünü çıkar
2. Config'deki referenceRoi json string'ini parçala ve Otonom Ölçekleme çarpanlarını hesapla
3. engine.py -> PathDeviationService.calculate_deviations(detections)
4. Her araç için boundingBox üzerinden anchor_point (Çapa) hesapla
5. Noktanın, ölçeklendirilmiş Polygon/Polyline'a olan dik uzamsal mesafesini bul
6. Hesaplanan sonuçları her bir detection'ın 'metadata' alanına ekle
7. build_response(context) -> PackageHelper -> PackageModel Response JSON
      |
      V
[Client/Pipeline] <- JSON Response (PathDeviationResponse with zenginleştirilmiş outputDetections)
```

---

## 8. Metodoloji ve Algoritmalar

### 8.1 Otonom Ölçekleme ve Uzamsal Sapma Hesabı
- Amaç: Platformun standart UI çizim koordinatlarıyla, oynatılan videonun gerçek çözünürlük pikselleri arasındaki kaymayı/boyut farkını otonom oranlayıp, araçların sapma mesafelerini sıfır hata payı ile gerçek zamanlı tespit etmek.

- Adımlar (numaralı):
  1. Videonun anlık metadata bilgisi (`width`, `height`) okunur.
  2. UI'dan (canvas) çizilen çokgenin referans boyutları ve nokta dizilimi JSON'dan ayrıştırılır.
  3. `scale_x = video_width / canvas_width` ve `scale_y = video_height / canvas_height` hesaplanır.
  4. Orijinal noktalar bu `scale` oranlarıyla çarpılarak gerçek konumlara adapte edilir.
  5. Her nesne (araç) için, kullanıcının seçtiği `triggeringAnchor` formülüne (Örn: left + width/2) göre bir merkezi (cx, cy) nokta bulunur.
  6. Merkezi noktanın, ölçeklendirilmiş doğrular dizisine olan en yakın matematiksel dik uzaklığı hesaplanır.
  7. Çıkan değer, `metadata.path_deviation` olarak atanır ve dönülür.

- Pseudo-code:
```python
def calculate_deviations(self, detections, raw_roi, video_width, video_height):
    # 1. Otonom Ölçekleme
    canvas_w, canvas_h, poly_points = parse_json_roi(raw_roi)
    scale_x = video_width / canvas_w
    scale_y = video_height / canvas_h
    
    scaled_path = [(x * scale_x, y * scale_y) for x, y in poly_points]
    
    # 2. Uzamsal Sapma
    for det in detections:
        anchor_x, anchor_y = get_anchor_point(det.boundingBox, anchor_type)
        min_distance = calculate_shortest_distance_to_polyline(anchor_x, anchor_y, scaled_path)
        
        # 3. Zenginleştirme
        det.metadata = {
            "path_deviation": round(min_distance, 2),
            "debug_reference_path": scaled_path
        }
        
    return detections
```

- Kullanılan algoritma detayları:
  - Uzamsal Hesaplama Formülleri: Geleneksel çizgi mesafesi yaklaşımları
  - Ölçekleme: Koordinat tabanlı çapraz (cross) çarpım (Dynamic aspect ratio mapping)

- Avantajlar:
  - ✅ Ekstra bir config menüsüne veya manuel ölçek katsayısına ihtiyaç bırakmaz (Otonom zeka)
  - ✅ Pikseller decode edilmediği için sıfır-gecikme (zero-latency) I/O Bypass sunar
  - ✅ Çıktılar NovaVision çizim düğümlerine (`Draw Keypoint`) uygun `debug_reference_path` yapısı ile aktarılır
