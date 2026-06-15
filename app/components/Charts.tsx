"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { PerformancePoint } from "@/app/lib/types";

export function RoiAreaChart({ data }: { data: PerformancePoint[] }) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="roiFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#1a936f" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#1a936f" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#d7ddd8" strokeDasharray="3 3" />
          <XAxis dataKey="label" tickLine={false} />
          <YAxis tickLine={false} />
          <Tooltip />
          <Area type="monotone" dataKey="profit" stroke="#1a936f" fill="url(#roiFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BucketBarChart({ data }: { data: PerformancePoint[] }) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid stroke="#d7ddd8" strokeDasharray="3 3" />
          <XAxis dataKey="label" tickLine={false} />
          <YAxis tickLine={false} />
          <Tooltip />
          <Bar dataKey="roi" fill="#2f6fbb" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

