import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { connectionsApi, Connection, ApiTokenData, LinkedInValidateResult } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { Link2, Key, CheckCircle, XCircle, AlertTriangle, Copy, Loader2, Plug, Webhook } from "lucide-react"

export default function ConnectionsPage() {
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const [liAtInput, setLiAtInput] = useState("")
  const [showTokenModal, setShowTokenModal] = useState(false)
  const [newToken, setNewToken] = useState<string | null>(null)
  const [showRevokeModal, setShowRevokeModal] = useState(false)

  const { data: connectionsData, isLoading: isLoadingConnections } = useQuery({
    queryKey: ["connections"],
    queryFn: () => connectionsApi.list(),
  })

  const linkedInConnection = connectionsData?.data?.connections?.find(
    (c: Connection) => c.type === "linkedin_cookie"
  )

  const saveLinkedInMutation = useMutation({
    mutationFn: (li_at: string) => connectionsApi.saveLinkedInCookie(li_at),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
      setLiAtInput("")
    },
  })

  const validateLinkedInMutation = useMutation({
    mutationFn: () => connectionsApi.validateLinkedIn(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
    },
  })

  const deleteLinkedInMutation = useMutation({
    mutationFn: () => connectionsApi.deleteLinkedInCookie(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
    },
  })

  const generateTokenMutation = useMutation({
    mutationFn: () => connectionsApi.generateApiToken(),
    onSuccess: (response) => {
      setNewToken(response.data.token)
      setShowTokenModal(true)
      queryClient.invalidateQueries({ queryKey: ["connections"] })
    },
  })

  const revokeTokenMutation = useMutation({
    mutationFn: () => connectionsApi.revokeApiToken(),
    onSuccess: () => {
      setShowRevokeModal(false)
      queryClient.invalidateQueries({ queryKey: ["connections"] })
    },
  })

  const handleSaveLinkedIn = async () => {
    if (!liAtInput.trim()) return
    await saveLinkedInMutation.mutateAsync(liAtInput)
    await validateLinkedInMutation.mutateAsync()
  }

  const handleValidateLinkedIn = async () => {
    await validateLinkedInMutation.mutateAsync()
  }

  const handleDeleteLinkedIn = async () => {
    await deleteLinkedInMutation.mutateAsync()
  }

  const handleGenerateToken = async () => {
    await generateTokenMutation.mutateAsync()
  }

  const handleRevokeToken = async () => {
    await revokeTokenMutation.mutateAsync()
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const getDaysRemainingColor = (days?: number) => {
    if (!days) return "default"
    if (days < 5) return "destructive"
    if (days < 10) return "secondary"
    return "default"
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Scrapped - Conexões</h1>
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-2">
                {user.picture && (
                  <img src={user.picture} alt={user.name} className="h-8 w-8 rounded-full" />
                )}
                <span className="text-sm font-medium">{user.name}</span>
              </div>
            )}
            <Button variant="ghost" size="icon" onClick={logout}>
              <Link2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5" />
                LinkedIn
              </CardTitle>
              <CardDescription>
                Cole o cookie li_at para autenticação no LinkedIn
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!linkedInConnection ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="liat">Cookie li_at</Label>
                    <Input
                      id="liat"
                      type="password"
                      placeholder="Cole o cookie li_at aqui"
                      value={liAtInput}
                      onChange={(e) => setLiAtInput(e.target.value)}
                    />
                  </div>
                  <Button
                    className="w-full"
                    onClick={handleSaveLinkedIn}
                    disabled={saveLinkedInMutation.isPending || !liAtInput.trim()}
                  >
                    {saveLinkedInMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Salvar e validar
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium text-green-800">
                          {linkedInConnection.days_remaining !== undefined && linkedInConnection.days_remaining > 0
                            ? `Ativa - expira em ${linkedInConnection.days_remaining} dias`
                            : "Ativa"}
                        </p>
                        {linkedInConnection.last_validated_at && (
                          <p className="text-xs text-green-600">
                            Última validação: {new Date(linkedInConnection.last_validated_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                    {linkedInConnection.days_remaining !== undefined && linkedInConnection.days_remaining < 10 && (
                      <Badge variant={linkedInConnection.days_remaining < 5 ? "destructive" : "secondary"}>
                        {linkedInConnection.days_remaining < 5 ? "< 5 dias" : "< 10 dias"}
                      </Badge>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={handleValidateLinkedIn}
                      disabled={validateLinkedInMutation.isPending}
                    >
                      {validateLinkedInMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Testar sessão
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setLiAtInput("")}
                      disabled={!liAtInput}
                    >
                      Atualizar cookie
                    </Button>
                    <Button variant="destructive" onClick={handleDeleteLinkedIn}>
                      Remover
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Token de API
              </CardTitle>
              <CardDescription>
                Token para acesso via API
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!connectionsData?.data?.api_token ? (
                <Button className="w-full" onClick={handleGenerateToken}>
                  Gerar token
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="p-3 bg-gray-50 border rounded-lg">
                    <p className="font-mono text-lg">{connectionsData.data.api_token.prefix}xxxxxxxxxxxxxxxx</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Criado em: {new Date(connectionsData.data.api_token.created_at).toLocaleString()}
                    </p>
                    {connectionsData.data.api_token.last_used_at && (
                      <p className="text-xs text-gray-500">
                        Último uso: {new Date(connectionsData.data.api_token.last_used_at).toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowRevokeModal(true)}
                    >
                      Revogar
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="h-5 w-5" />
                Webhook
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="secondary">Em breve</Badge>
            </CardContent>
          </Card>

          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plug className="h-5 w-5" />
                Zapier / n8n
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="secondary">Em breve</Badge>
            </CardContent>
          </Card>
        </div>
      </main>

      {showTokenModal && newToken && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Token de API Gerado</h2>
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
              <p className="text-yellow-800 font-medium mb-2">⚠️ Importante:</p>
              <p className="text-yellow-700 text-sm">
                Este token não poderá ser visualizado novamente. Copie agora.
              </p>
            </div>
            <div className="flex gap-2 mb-4">
              <code className="flex-1 p-3 bg-gray-100 rounded-lg font-mono text-sm break-all">
                {newToken}
              </code>
              <Button variant="outline" size="icon" onClick={() => copyToClipboard(newToken)}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button className="w-full" onClick={() => setShowTokenModal(false)}>
              Copiei o token
            </Button>
          </div>
        </div>
      )}

      {showRevokeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Revogar Token</h2>
            <p className="text-gray-600 mb-4">
             Tem certeza que deseja revogar o token de API? Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setShowRevokeModal(false)}>
                Cancelar
              </Button>
              <Button variant="destructive" onClick={handleRevokeToken}>
                Revogar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}