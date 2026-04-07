import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authApi } from "@/lib/api"
import { Mail, Lock, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/lib/auth"

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, login } = useAuth()
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard")
    }
  }, [isAuthenticated, navigate])

  const handleGoogleLogin = async () => {
    setLoading(true)
    setError("")
    try {
      const authUrl = await authApi.getGoogleAuthUrl()
      window.location.href = authUrl
    } catch (error) {
      console.error("Failed to get Google auth URL:", error)
      setLoading(false)
    }
  }

  const handleEmailLogin = async () => {
    if (!email || !password) {
      setError("Please fill in all fields")
      return
    }
    
    setLoading(true)
    setError("")
    
    try {
      const response = await authApi.login(email, password)
      localStorage.setItem("access_token", response.data.access_token)
      localStorage.setItem("refresh_token", response.data.refresh_token)
      navigate("/dashboard")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed")
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email || !password || !name) {
      setError("Please fill in all fields")
      return
    }
    
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }
    
    setLoading(true)
    setError("")
    
    try {
      const response = await authApi.register(email, password, name)
      localStorage.setItem("access_token", response.data.access_token)
      localStorage.setItem("refresh_token", response.data.refresh_token)
      navigate("/dashboard")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed")
      setLoading(false)
    }
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
          {isRegister ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button 
                className="w-full" 
                size="lg" 
                onClick={handleRegister}
                disabled={loading}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Register
              </Button>
              <div className="text-center text-sm">
                Already have an account?{" "}
                <button 
                  onClick={() => { setIsRegister(false); setError("") }}
                  className="text-primary hover:underline"
                >
                  Sign in
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    className="pl-10"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Password"
                    className="pl-10"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button 
                className="w-full" 
                size="lg" 
                onClick={handleEmailLogin}
                disabled={loading}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Sign in with Email
              </Button>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or
                  </span>
                </div>
              </div>
              <Button 
                className="w-full" 
                size="lg" 
                variant="outline"
                onClick={handleGoogleLogin}
                disabled={loading}
              >
                {loading ? "Redirecting..." : "Sign in with Google"}
              </Button>
              <div className="text-center text-sm">
                Don't have an account?{" "}
                <button 
                  onClick={() => { setIsRegister(true); setError("") }}
                  className="text-primary hover:underline"
                >
                  Register
                </button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}