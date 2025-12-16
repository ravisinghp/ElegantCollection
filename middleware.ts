// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const hasSession = request.cookies.get("insideApp")?.value;

  // Define only the public routes that can be opened directly
  const publicRoutes = ["/login", "/reset-password"];

  // Redirect /reset-password → /login with reset query param
  if (path.startsWith("/reset-password")) {
    const url = new URL("/login", request.url);
    url.searchParams.set("reset", "true");

    // preserve token if present
    const token = request.nextUrl.searchParams.get("token");
    if (token) url.searchParams.set("token", token);

    return NextResponse.redirect(url);
  }

  //  If trying to access *any* other route by URL → force redirect to /login
  if (!publicRoutes.includes(path)) {
    // Only allow if there’s a session cookie
    if (!hasSession) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  // Match everything inside your app except Next.js internals
  matcher: ["/((?!_next|api|static|.*\\..*).*)"],
};
