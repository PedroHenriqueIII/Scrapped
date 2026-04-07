import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { searchApi, DecisionMaker, SearchStatus } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { Search, Upload, History, LogOut, Loader2, Link2 } from "lucide-react"
import { Link } from "react-router-dom"

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const [query, setQuery] = useState("")
  const [targetRole, setTargetRole] = useState("")
  const [searchId, setSearchId] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)

  const { data: searchHistory, refetch: refetchHistory } = useQuery({
    queryKey: ["searchHistory"],
    queryFn: () => searchApi.list(0, 10),
  })

  const { data: searchResult, isLoading: isLoadingResult } = useQuery({
    queryKey: ["search", searchId],
    queryFn: () => searchApi.get(searchId!),
    enabled: !!searchId,
    refetchInterval: () => {
      const status = searchResult?.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 3000;
    },
  })

  const handleSearch = async () => {
    if (!query.trim()) return
    setIsSearching(true)
    setSearchId(null)
    
    try {
      const response = await searchApi.create(query, targetRole || undefined)
      setSearchId(response.data.id)
      refetchHistory()
    } catch (error) {
      console.error("Search failed:", error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleLogout = async () => {
    await logout()
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="default">Completed</Badge>
      case "processing":
        return <Badge variant="secondary">Processing</Badge>
      case "pending":
        return <Badge variant="outline">Pending</Badge>
      case "failed":
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Scrapped</h1>
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-2">
                {user.picture && (
                  <img 
                    src={user.picture} 
                    alt={user.name} 
                    className="h-8 w-8 rounded-full"
                  />
                )}
                <span className="text-sm font-medium">{user.name}</span>
              </div>
            )}
            <Button variant="ghost" size="icon" asChild>
              <Link to="/connections">
                <Link2 className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Search Decision Makers
                </CardTitle>
                <CardDescription>
                  Enter a company name, CNPJ, location, or person name
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="query">Search Query</Label>
                  <Input
                    id="query"
                    placeholder="e.g., All About Energy, 12.345.678/0001-90, eventos Fortaleza"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Target Role (Optional)</Label>
                  <Input
                    id="role"
                    placeholder="e.g., CEO, Director, Manager"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleSearch} 
                  disabled={isSearching || !query.trim()}
                >
                  {isSearching ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    "Search"
                  )}
                </Button>
              </CardContent>
            </Card>

            {searchId && (
              <Card>
                <CardHeader>
                  <CardTitle>Results</CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingResult || !searchResult?.data ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-muted-foreground">
                        Processing search...
                      </span>
                    </div>
                  ) : searchResult.data.status === "completed" ? (
                    searchResult.data.results.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">
                        No results found
                      </p>
                    ) : (
                      <div className="space-y-4">
                        {searchResult.data.results.map((result: DecisionMaker) => (
                          <div
                            key={result.id}
                            className="p-4 border rounded-lg space-y-2"
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="font-semibold">{result.name}</h3>
                                <p className="text-sm text-muted-foreground">
                                  {result.role} at {result.company}
                                </p>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold text-primary">
                                  {result.confidence_score}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  confidence
                                </div>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              {result.sources?.map((source: string) => (
                                <Badge key={source} variant="outline">
                                  {source}
                                </Badge>
                              ))}
                            </div>
                            {(result.email || result.phone || result.linkedin_url) && (
                              <div className="pt-2 border-t text-sm space-y-1">
                                {result.email && (
                                  <p>
                                    <span className="font-medium">Email:</span>{" "}
                                    {result.email}
                                  </p>
                                )}
                                {result.phone && (
                                  <p>
                                    <span className="font-medium">Phone:</span>{" "}
                                    {result.phone}
                                  </p>
                                )}
                                {result.linkedin_url && (
                                  <p>
                                    <span className="font-medium">LinkedIn:</span>{" "}
                                    <a
                                      href={result.linkedin_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-primary hover:underline"
                                    >
                                      Profile
                                    </a>
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )
                  ) : (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-muted-foreground">
                        {searchResult.data.status === "processing" 
                          ? "Processing..." 
                          : searchResult.data.status}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Recent Searches
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!searchHistory?.data?.searches?.length ? (
                  <p className="text-muted-foreground text-sm">No recent searches</p>
                ) : (
                  <div className="space-y-2">
                    {searchHistory.data.searches.map((search: SearchStatus) => (
                      <div
                        key={search.id}
                        className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                        onClick={() => setSearchId(search.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-medium line-clamp-1">
                              Click to view results
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(search.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          {getStatusBadge(search.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Batch Search
                </CardTitle>
                <CardDescription>
                  Upload a CSV file with multiple queries
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  Upload CSV
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}