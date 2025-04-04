// src/app/api/health/route.ts
import { NextResponse } from 'next/server';

export const dynamic = 'force-static'; // Ensures no server-side computation

export async function GET() {
  return NextResponse.json(
    { status: 'ok', timestamp: new Date().toISOString() },
    { status: 200 }
  );
}

// Explicitly handle HEAD requests (UptimeRobot's default)
export async function HEAD() {
  return new NextResponse(null, { status: 200 });
}