import { NextResponse } from "next/server";
import { createServiceClient } from "@/app/lib/supabase";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = createServiceClient();
  const { data, error } = await supabase
    .from("bet_results")
    .select("result_date, stake_units, profit_units, clv, outcome")
    .order("result_date", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ results: data ?? [] });
}

