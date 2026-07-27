import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "法人税・別表四シミュレーター",
  description:
    "試算表から税務調整を行い、課税所得と法人税等を試算する MVP アプリケーション",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
