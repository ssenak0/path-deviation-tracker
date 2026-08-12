# Path Deviation Tracker (Yol Sapması Takibi)

Bu proje, NovaVision platformu üzerinde çalışan otonom bir **Veri Analiz (Analytics) Kapsülü**dür. Amacı, bir video akışı içerisindeki hareketli nesnelerin (örneğin araçların) önceden belirlenmiş bir referans rotasına olan sapma miktarını (path deviation) gerçek zamanlı olarak hesaplamaktır.

Kapsül, bir "Görüntü İşleme" modülü **değildir**. Gelen video piksellerini manipüle etmez. Yalnızca `Object Tracking` modülünden gelen sınır kutularını (bounding box) ve araç kimliklerini (`trackerID`) kullanarak matematiksel analiz yapar. 

## 🚀 Proje Nasıl Çalışır?

1. **Veri Toplama:** Kapsül, `Video Feed` düğümünden anlık kareleri (gerçek video çözünürlüğünü tespit etmek ve otonom ölçekleme yapmak için) ve `Object Tracking` düğümünden araçların güncel koordinatlarını (`detections`) alır.
2. **Çapa Noktası (Anchor) Tespiti:** Tespit edilen her bir aracın sınır kutusu (bounding box) üzerinden, kullanıcının seçtiği referans çapa noktası (Örn: `CENTER`, `TOP_CENTER` veya `BOTTOM_CENTER`) hesaplanır.
3. **Sapma Hesaplaması:** Aracın çapa noktası ile kullanıcının arayüzden çizdiği referans şekli (çizgi veya çokgen) arasındaki en kısa dik mesafe (path deviation) hesaplanır.
4. **Veri Zenginleştirme:** Hesaplanan bu sapma değeri ve ölçeklendirilmiş referans koordinatları, aracın verisine `metadata` olarak kalıcı şekilde eklenir (`path_deviation` ve `debug_reference_path`).
5. **Çıktı:** Zenginleştirilmiş bu yeni tespit listesi (`outputDetections`), görselleştirme (çizim) amacıyla akıştaki bir sonraki düğüme (`Draw Bounding Box`) iletilerek analiz zinciri tamamlanır.

## ⚡ Son Dönem Geliştirmeleri ve Optimizasyonlar

- **Otonom Çözünürlük ve Ölçekleme (Auto-Scaling):** Çizim yapılan tuvalin (canvas) boyutları ile gerçek videonun çözünürlüğü arasındaki piksel uyuşmazlığı tamamen giderilmiştir. Gelen arayüz (JSON) verisi ayrıştırılır ve videonun gerçek ölçülerine (1080p, 4K vb.) göre dinamik olarak oranlanır. Kullanıcının manuel bir "Scale" katsayısı girmesine gerek kalmamıştır.
- **Native Component Mimarisi:** NovaVision SDK gereksinimlerini karşılamak üzere kapsül, `Component` temel sınıfı üzerine inşa edilmiştir. İçe aktarma (import) yolları doğrudan `src` modülü üzerinden yapılandırılarak `ModuleNotFoundError` riskleri tamamen giderilmiştir.
- **Yüksek Performanslı I/O Bypassi:** Bu kapsül, sadece koordinat hesabı yaptığı için standart Redis `get_frame` ve `set_frame` okuma/yazma döngüleri koddan çıkartılmıştır. Ağ yükü sıfırlanmış ve saniye-kare (FPS) hızı maksimize edilmiştir.

---

## 🛠 NovaVision Üzerinde Nasıl Çalıştırılır?

Bu kapsülü NovaVision platformunda çalıştırabilmek için bir Flow (Akış) oluşturmanız gerekmektedir. Akış bağlantılarınızı ve parametrelerinizi aşağıdaki gibi ayarlamalısınız:

### 1. Düğüm (Node) Bağlantıları (Flow)

Ekran görüntüsündeki akışa göre düğüm bağlantılarını şu şekilde kurmalısınız:

* **Video Feed (Image)** ➔ **YOLO Inference** (`inputImage`) portuna.
* **Video Feed (Image)** ➔ **Object Tracking** (`inputImage`) portuna.
* **Video Feed (Image)** ➔ **Path Deviation Tracker** (`inputImage`) portuna.
* **Video Feed (Image)** ➔ **Draw Bounding Box** (`inputImage`) portuna.
* **YOLO Inference (Detections)** ➔ **Object Tracking** (`detections`) portuna.
* **Object Tracking (Detections)** ➔ **Path Deviation Tracker** (`detections`) portuna.
* **Path Deviation Tracker (Detections)** ➔ **Draw Bounding Box** (`inputDetections`) portuna.
* **Draw Bounding Box (Image)** ➔ **Draw Keypoint** (`inputImage`) portuna.
* **Draw Bounding Box (Detections)** ➔ **Draw Keypoint** (`inputDetections`) portuna.
* **Draw Keypoint (Image)** ➔ **Video View** (`inputImage`) portuna.

> **Önemli:** `Path Deviation Tracker` herhangi bir görsel (Image) çıktısı üretmez, yalnızca `outputDetections` (koordinat listesi) çıktısı verir. Bu nedenle `Draw Bounding Box` ana görüntüyü doğrudan `Video Feed` üzerinden almalıdır. Sonrasında `Draw Bounding Box` hem görseli hem de tespit verilerini `Draw Keypoint`'e aktararak görselleştirme zincirini tamamlar.

### 2. Kapsül Parametreleri (Configs)

Kapsülü (Node) platform üzerinde seçtiğinizde yandaki ayarlardan şu parametreleri doldurmalısınız:

- **`referenceRoi` (Draw Reference Path)**: Sapmanın ölçüleceği referans rotasını belirten gelişmiş arayüz çizim aracıdır. Ekranda farenizle çizdiğiniz Polygon (Çokgen) veya Polyline (Çizgi) şeklinin koordinatları otomatik olarak kod tarafından algılanıp videoya ölçeklendirilir. Artık elle sayı (JSON) veya Scale oranı girmenize gerek yoktur.
- **`triggeringAnchor`**: Sınır kutusunun (aracın) neresinin merkez noktası olarak kabul edileceği. Değerler: `CENTER`, `TOP_CENTER` veya `BOTTOM_CENTER`. Yolla olan mesafenin daha doğru (zemin teması) ölçülmesi için genellikle `BOTTOM_CENTER` önerilir.

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
    "path_points": 1,
    "debug_reference_path": [
      [962.8, 112.59],
      [901.6, 950.17],
      [1021.75, 950.17],
      [1008.84, 108.0]
    ]
  }
}
```

Bu veri yapısını alan `Draw Keypoint` düğümü, `debug_reference_path` üzerindeki koordinatları okuyarak ekranda çizgiyi başarılı bir şekilde çizer. Diğer platform araçlarıyla ise `path_deviation` değerine bakılarak araçların şeritten taşıp taşmadığına dair alarmlar üretilebilir.

---

## 📁 Proje Yapısı

- `src/models/PackageModel.py`: NovaVision SDK ile tam uyumlu kapsül modeli, parametre tipleri ve girdi/çıktı tanımları (Pydantic şemaları). Otonom ölçekleme entegrasyonu nedeniyle eski `roiScale` gereksinimi buradan kaldırılmıştır.
- `src/executors/PathDeviationTrackerExecutor.py`: Modülün can damarı olan ana çalıştırıcı sınıf. Video Feed'den alınan meta veriler üzerinden Otonom Ölçekleme (Auto-Scaling) matematiğini gerçekleştirir, verileri `PathDeviationService` motoruna besler ve JSON yanıtı döndürür.
- `src/utils/engine.py`: İki nokta veya çokgen (Polygon) arası mesafe hesaplama, çizim görselleştirme (Draw Keypoint desteği) ve `trackerID` bellek yönetimini gerçekleştiren servis sınıfı.
- `src/utils/response.py`: Çıkan veriyi SDK'nın beklediği formata sararak `PackageHelper` aracılığıyla dönüştüren yardımcı metot.
