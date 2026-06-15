import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    ok: true,
    service: "mlb-kalshi-edge",
    ts: new Date().toISOString()
  });
}

