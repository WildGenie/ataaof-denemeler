
import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.shared import clean_html

raw_title = """<p>Düz İleri tekniğinde animasyona en baştan başlayıp adım adım, istenilen hareket tamamlanana kadar<br />sıralı olarak bir sonraki hareket anı oluşturulur. “Düz İleri animasyonun ilk pozuyla başlar ve hareket sonuna<br />kadar adım adım geliştirilir” (Bühler, Schlaich ve Sinner, 2017: 4). Düz İleri animasyonunu hareketin<br />türüne göre kullanmak gerekse de genelde hata yapmaya en açık yöntemdir ve ustalık gerektirir. Bu tekniğin<br />en büyük avantajı, sunduğu serbestlik ve doğaçlamaya açık olmasıdır. Bu nedenle Düz İleri tekniği genelde<br />deneysel çalışmalarda kullanılır. Webster’in (2005: 26) de belirttiği gibi Düz İleri tekniği, animasyona aşırı<br />planlı bir yaklaşımla engel olmaz, hareketi akışa bırakmak mümkün olur. Bu, farklı ögelerin kendi zamanlamalarına<br />sahip olduğu birden fazla hareket içeren eylemlerde çok kullanışlıdır. Öte yandan, bu durum<br />animatörün üzerinde büyük bir baskı yaratır, çünkü mevcut bir sekansın içine kareler ekleyerek düzeltme<br />yapmak kolay bir iş değildir (W"""

print("--- Original Title ---")
print(repr(raw_title))

cleaned = clean_html(raw_title)
print("\n--- Cleaned Title ---")
print(repr(cleaned))

if "yapmak kolay bir iş değildir" in cleaned:
    print("\nSUCCESS: Text is fully preserved.")
else:
    print("\nFAILURE: Text is truncated.")
