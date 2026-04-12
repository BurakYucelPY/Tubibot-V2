import { ChangelogArticle } from "@/components/landing/ChangelogArticle";
import { LandingLayout } from "@/components/landing/Layout";

export default function LandingPage() {
  return (
    <LandingLayout>
      <ChangelogArticle
        id="2504-tubitak-cnr-italya"
        date="2026-04-11T00:00Z"
      >
        <div className="relative overflow-hidden rounded-xl bg-gray-50 dark:bg-gray-900">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://tubitak.gov.tr/sites/default/files/styles/original/public/2026-04/2504-TUBITAK_ITALYA_web_0.jpg.webp?itok=GdPCq6Qv"
            alt="2504 TÜBİTAK–CNR İtalya İkili İş Birliği Çağrısı"
            className="w-full"
          />
          <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-gray-900/10 ring-inset dark:ring-white/10" />
        </div>
        <h2>2504 TÜBİTAK–CNR (İtalya) İkili İş Birliği Çağrısı Açıldı</h2>
        <p>
          TÜBİTAK ve İtalya Ulusal Araştırma Kurumu (Italy National Research
          Council-CNR) tarafından araştırma projeleri için ikili iş birliği
          çağrısı yayınlandı.
        </p>
      </ChangelogArticle>

      <ChangelogArticle
        id="1833-sayem-yesil-donusum"
        date="2026-04-10T00:00Z"
      >
        <div className="relative overflow-hidden rounded-xl bg-gray-50 dark:bg-gray-900">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://tubitak.gov.tr/sites/default/files/styles/original/public/2026-04/TEYDEB_1833_web-2026.jpg.webp?itok=ZqwRP5GM"
            alt="1833 SAYEM Yeşil Dönüşüm 2026-1 Çağrısı"
            className="w-full"
          />
          <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-gray-900/10 ring-inset dark:ring-white/10" />
        </div>
        <h2>1833 SAYEM Yeşil Dönüşüm 2026-1 Çağrısı 2. Aşaması Başvuruya Açıldı</h2>
        <p>
          1833 SAYEM Yeşil Dönüşüm 2026-1 Çağrısı&rsquo;nın ikinci aşaması
          başvuruya açılmış olup başvuru süreci ve koşullarında önemli
          güncellemeler yapılmıştır.
        </p>
      </ChangelogArticle>

      <ChangelogArticle
        id="dikey-inisli-roket-yarismasi"
        date="2026-04-09T00:00Z"
      >
        <div className="relative overflow-hidden rounded-xl bg-gray-50 dark:bg-gray-900">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://tubitak.gov.tr/sites/default/files/styles/original/public/2026-04/dikey-inisli-roket-2_web.jpg.webp?itok=i0kDL3Lt"
            alt="Dikey İnişli Roket Yarışması"
            className="w-full"
          />
          <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-gray-900/10 ring-inset dark:ring-white/10" />
        </div>
        <h2>Dikey İnişli Roket Yarışması Ön Tasarım Raporu Sonuçları Açıklandı</h2>
        <p>
          TEKNOFEST kapsamında düzenlenen Dikey İnişli Roket Yarışması&rsquo;nın
          &ldquo;Ön Tasarım Raporu&rdquo; aşamasında başarılı olan takımlar bir
          sonraki adım olarak &ldquo;Kritik Tasarım Raporu&rdquo; yükleyecekler.
        </p>
      </ChangelogArticle>
    </LandingLayout>
  );
}
