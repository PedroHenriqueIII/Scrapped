import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { authApi } from "@/lib/api"
import { Mail } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

export default function LoginPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (token) {
      navigate("/dashboard")
    }
  }, [navigate])

  const handleLogin = () => {
    setLoading(true)
    authApi.login()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl">Scrapped</CardTitle>
          <CardDescription>
            Intelligence Platform for Business Decision Makers
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-sm text-muted-foreground">
            Sign in with your Google account to access the platform
          </div>
          <Button 
            className="w-full" 
            size="lg" 
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? "Redirecting..." : "Sign in with Google"}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}