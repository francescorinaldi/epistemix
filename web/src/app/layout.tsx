import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Epistemix — Epistemic Audit Framework",
  description:
    "Detect unknown unknowns in research. Predict what knowledge should exist, then verify whether it does.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div id="app">{children}</div>
      </body>
    </html>
  );
}
