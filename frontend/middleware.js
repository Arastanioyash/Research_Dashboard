import { NextResponse } from 'next/server';

export function middleware(req) {
  const token = req.cookies.get('rd_token')?.value;
  const { pathname } = req.nextUrl;

  if ((pathname.startsWith('/app') || pathname.startsWith('/admin')) && !token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  if (pathname === '/login' && token) {
    return NextResponse.redirect(new URL('/app', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/app/:path*', '/admin/:path*', '/login']
};
