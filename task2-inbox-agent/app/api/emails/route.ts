import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const filePath = path.resolve(process.cwd(), "data", "emails.json");
    const raw = fs.readFileSync(filePath, "utf-8");
    const emails = JSON.parse(raw);
    return NextResponse.json(emails);
  } catch (error) {
    return NextResponse.json({ error: "Failed to read emails" }, { status: 500 });
  }
}
