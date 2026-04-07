import { useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"

export default function CallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const token = searchParams.get("token")
    if (token) {
      localStorage.setItem("token", token)
      navigate("/dashboard")
    } else {
      navigate("/login")
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