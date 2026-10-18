import "./globals.css";
import React from "react";

export const metadata = {
  title: "Inbox Agent (T2) - AI Tech Consultant",
  description: "Autonomous Email Triaging, Grounded Drafting & Human Review Suite",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-emerald-soft selection:text-emerald-deep">
        {children}
      </body>
    </html>
  );
}
