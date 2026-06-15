import { NextRequest, NextResponse } from "next/server";
import { env } from "@/app/lib/env";

export async function GET(request: NextRequest) {
  const configuredSecret = env.cronSecret();
  if (configuredSecret) {
    const auth = request.headers.get("authorization");
    const userAgent = request.headers.get("user-agent") ?? "";
    const isVercelCron = userAgent.includes("vercel-cron");
    if (auth !== `Bearer ${configuredSecret}` && !isVercelCron) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  }

  return NextResponse.json({
    ok: true,
    message:
      "Daily model execution is intentionally handled by GitHub Actions. This Vercel cron endpoint is a deployment smoke check.",
    ts: new Date().toISOString()
  });
}
