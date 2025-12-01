
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.shared import clean_html

raw_explanation = """<div class=\"page\" data-page-number=\"10\" data-page-label=\"235\" data-loaded=\"true\">\n<div class=\"textLayer\">S\u001enemada zamanı ele aldıgımızda “Reel (astronom<br />\u001fk) Zaman”, “Kurgusal (\u001frreel) Zaman” ve<br />“Hayal\u001f (mevhum) Zaman” olmak üzere üçe ayırmak<br />mümkündür. Reel zaman, f\u001elmde geçen süren<br />\u001en gerçek zamanla uyum hâl\u001ende oldugu zaman<br />türüdür. Örneg\u001en; f\u001elmde b\u001er karakter\u001en koltuktan<br />kalkarak mutfaga g\u001etme süres\u001e gerçek zamanla b\u001ere<br />b\u001er uyum hâl\u001ende olur. Kurgusal zaman; f\u001elmde<br />geçen b\u001er zaman d\u001el\u001em\u001en\u001en, öznel çek\u001emlerle ya<br />da kurgu yoluyla gerçek zamana göre kısaltılması<br />veya uzatılmasıdır. Dem\u001er’\u001en (1994: 6) de bel\u001ertt<br />\u001eg\u001e g\u001eb\u001e gerçek zamanda ve mekânda yapılan bu<br />seçmeler aks\u001eyonun gel\u001es\u001em\u001ende en öneml\u001e unsurdur.<br />Kurgusal zamana saatler sürecek b\u001er yolculugun<br />baslangıcı ve b\u001et\u001es\u001ene \u001el\u001esk\u001en görüntüler\u001en<br />kurgu yoluyla kısaltılmasını ya da b\u001er kovalama<br />anının farklı açılardan farklı planlarla görüntülenerek<br />ekranda hız ve heyecan yaratmasını örnek<br />olarak vermek mümkündür. Hayal\u001e zaman \u001ese<br />daha çok b\u001el\u001em kurgu f\u001elmlerde görülen, nasıl ve<br />ne zaman oldugu bell\u001e olmayan zaman türüdür.<br />Bunun yanı sıra f\u001elmdek\u001e kahramanlardan b\u001er\u001en\u001en<br />düsünceler\u001e ya da \u001estekler\u001e görsellest\u001er\u001eld\u001eg\u001ende<br />bu da hayal\u001e zaman olarak n\u001etelend\u001er\u001el\u001er. S\u001enema<br />dogası gereg\u001e reel zaman ve hayal\u001e zamanı aynı<br />anda görsellest\u001ereb\u001elmekted\u001er. Örneg\u001en; 3 dak\u001eka<br />10 san\u001eye süren b\u001er sekansın \u001es\u001etsel boyutunda 3<br />dak\u001eka 10 san\u001eyel\u001ek b\u001er müz\u001ek parçasının çalması<br />o sekansa \u001el\u001esk\u001en reel zamanın \u001efades\u001e \u001eken sekansın<br />görsel \u001eçer\u001eg\u001ende yaratılan hayal\u001e zaman daha<br />uzun ya da daha kısa olab\u001elmekted\u001er ( Doğru cevap D'dir.</div>\n</div>\n<div class=\"page\" data-page-number=\"11\" data-page-label=\"236\" data-loaded=\"true\">\n<div class=\"canvasWrapper\"> </div>\n<div class=\"textLayer\"> </div>\n</div>"""

print("--- Original Explanation ---")
print(repr(raw_explanation))

cleaned = clean_html(raw_explanation)
print("\n--- Cleaned Explanation ---")
print(repr(cleaned))
