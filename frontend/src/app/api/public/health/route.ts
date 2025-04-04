// src/app/api/health/route.ts
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Ensures no server-side computation

export async function GET() {
  return NextResponse.json(
    { status: 'ok', timestamp: new Date().toISOString() },
    { status: 200 }
  );
}