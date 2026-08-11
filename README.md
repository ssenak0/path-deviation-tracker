# Path Deviation Tracker (Yol Sapması Takibi)

Bu proje, NovaVision platformu üzerinde çalışan otonom bir **Veri Analiz (Analytics) Kapsülü**dür. Amacı, bir video akışı içerisindeki hareketli nesnelerin (örneğin araçların) önceden belirlenmiş bir referans rotasına olan sapma miktarını (path deviation) gerçek zamanlı olarak hesaplamaktır.

Kapsül, bir "Görüntü İşleme" modülü **değildir**. Gelen video piksellerini manipüle etmez. Yalnızca ObjectTracking modülünden gelen sınır kutularını (bounding box) ve araç kimliklerini (`trackerID`) kullanarak matematiksel analiz yapar. 

## 🚀 Proje Nasıl Çalışır?

1. **Veri Toplama:** Kapsül, `VideoFeed` düğümünden anlık kareleri (senkronizasyon için) ve `ObjectTracking` düğümünden araçların koordinatlarını alır.
2. **Çapa Noktası (Anchor) Tespiti:** Gelen araçların sınır kutusu üzerinden belirlenen çapa noktası (Örn: `CENTER` veya `BOTTOM_CENTER`) bulunur.
3. **Sapma Hesaplaması:** Aracın çapa noktası ile kullanıcının belirlediği referans çizgisi (`reference_path`) arasındaki en kısa mesafe piksel bazında hesaplanır.
4. **Veri Zenginleştirme:** Hesaplanan bu sapma değeri, aracın verisine `metadata` olarak eklenir (`path_deviation: 1001.02` vb.).
5. **Çıktı:** Zenginleştirilmiş bu yeni tespit listesi (`outputDetections`), görselleştirme veya uyarı amacıyla bir sonraki düğüme (örneğin `DrawBoundingBox`) iletilir.

## ⚡ Son Dönem Geliştirmeleri ve Optimizasyonlar

- **Native Component Mimarisi:** NovaVision SDK gereksinimlerini karşılamak üzere kapsül, `Component` temel sınıfı üzerine inşa edilmiştir. İçe aktarma (import) yolları doğrudan `src` modülü üzerinden yapılandırılarak `ModuleNotFoundError` riskleri tamamen giderilmiştir.
- **Yüksek Performanslı I/O Bypassi:** Bu kapsül, sadece koordinat hesabı yaptığı için standart Redis `get_frame` ve `set_frame` okuma/yazma döngüleri koddan çıkartılmıştır. Ağ yükü sıfırlanmış ve saniye-kare (FPS) hızı maksimize edilmiştir.
- **Otonom Tekil Kamera Senaryosu:** Sistem, sabit bir kamera görüntüsü üzerinden çalışacak şekilde ayarlanmıştır. Hata fırlatmaya müsait olan katı "Kamera Kimliği" (`video_identifier`) meta-veri doğrulama süreçleri koddan kaldırılarak sistem tamamen otonom ve kesintisiz hale getirilmiştir.

---

## 🛠 NovaVision Üzerinde Nasıl Çalıştırılır?

Bu kapsülü NovaVision platformunda çalıştırabilmek için bir Flow (Akış) oluşturmanız gerekmektedir. Akış bağlantılarınızı ve parametrelerinizi aşağıdaki gibi ayarlamalısınız:

### 1. Düğüm (Node) Bağlantıları (Flow)

* **VideoFeed (Image)** ➔ PathDeviationTracker (`inputImage`) portuna.
* **ObjectTracking (Detections)** ➔ PathDeviationTracker (`detections`) portuna.
* **PathDeviationTracker (Detections)** ➔ DrawBoundingBox (`inputDetections`) portuna.
* **VideoFeed (Image)** ➔ DrawBoundingBox (`inputImage`) portuna.

> **Önemli:** `DrawBoundingBox` (veya başka bir çizim modülü) resmi PathDeviation üzerinden değil, **doğrudan VideoFeed üzerinden** almalıdır. PathDeviation yalnızca `outputDetections` (koordinat listesi) çıktısı verir.

### 2. Kapsül Parametreleri (Configs)

Kapsülü (Node) platform üzerinde seçtiğinizde yandaki ayarlardan şu parametreleri doldurmalısınız:

- **`referencePath`**: Sapmanın ölçüleceği referans rotasını belirten, JSON formatında bir nokta listesi (Örn: `[[100, 320], [200, 320], [300, 320]]`). Minimum iki nokta girilmelidir.
- **`triggeringAnchor`**: Sınır kutusunun neresinin arabanın konumu olarak kabul edileceği. Değerler: `CENTER`, `TOP_CENTER` veya `BOTTOM_CENTER`. Genellikle zemin teması için `BOTTOM_CENTER` önerilir.

### 3. Çıktı Formatı Beklentisi

Sistem çalıştığında, ürettiği `outputDetections` içindeki her bir araç nesnesinin sonuna aşağıdaki gibi bir **metadata** bloğu yerleştirilir:

```json
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
    "path_points": 1
  }
}
```

Bu veri yapısını alarak diğer platform analiz araçlarıyla araçların şeritten taşıp taşmadığına dair alarmlar üretebilirsiniz.

---

## 📁 Proje Yapısı

- `src/models/PackageModel.py`: NovaVision SDK ile tam uyumlu kapsül modeli, veri tipleri ve girdi/çıktı tanımları (Pydantic şemaları).
- `src/executors/PathDeviationTrackerExecutor.py`: Modülün can damarı olan ana çalıştırıcı sınıf. Verileri karşılar, `PathDeviationService` motorunu tetikler ve JSON yanıtı döndürür.
- `src/utils/engine.py`: İki nokta arası mesafe hesaplama, sapma mantığı ve `trackerID` sözlüğü (belleği) yönetimini gerçekleştiren servis sınıfı.
- `src/utils/response.py`: Çıkan veriyi SDK'nın beklediği formata sararak `PackageHelper` aracılığıyla dönüştüren yardımcı metot.
