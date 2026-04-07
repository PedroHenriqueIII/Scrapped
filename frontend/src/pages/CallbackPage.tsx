import { useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"

export default function CallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const accessToken = searchParams.get("access_token")
    const refreshToken = searchParams.get("refresh_token")

    if (accessToken && refreshToken) {
      localStorage.setItem("access_token", accessToken)
      localStorage.setItem("refresh_token", refreshToken)
      
      window.history.replaceState({}, document.title, "/auth/callback")
      
      navigate("/dashboard")
    } else {
      navigate("/login?error=auth_failed")
    }
  }, [navigate, searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Authenticating...</p>
      </div>
    </div>
  )
}