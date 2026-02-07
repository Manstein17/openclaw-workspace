import { withAuth } from "next-auth/middleware"
import { NextResponse } from "next/server"

export default withAuth(
  function middleware(req) {
    // 如果用户已登录，允许访问
    return NextResponse.next()
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        // 检查用户是否有有效的 token
        // 只有访问 /dashboard 和 /api/user 时需要登录
        const path = req.nextUrl.pathname
        if (path.startsWith("/dashboard") || path.startsWith("/api/user")) {
          return !!token
        }
        return true
      },
    },
  }
)

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/api/user/:path*",
  ],
}
