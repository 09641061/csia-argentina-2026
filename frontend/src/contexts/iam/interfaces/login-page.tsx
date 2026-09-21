import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Alert, AlertDescription } from '@/shared/interfaces/ui/alert'
import { Button } from '@/shared/interfaces/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/shared/interfaces/ui/card'
import { Field, FieldGroup, FieldLabel } from '@/shared/interfaces/ui/field'
import { Input } from '@/shared/interfaces/ui/input'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { useAuth } from '@/contexts/iam/interfaces/auth-context'
import { AuthShell } from '@/contexts/iam/interfaces/auth-shell'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(username, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from && from.startsWith('/') ? from : '/', { replace: true })
    } catch (caught) {
      setError(apiErrorMessage(caught))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthShell>
      <Card className="w-full max-w-md rounded-[22px] border-white/[0.08] bg-[#242422] p-1 shadow-[0_24px_80px_rgba(0,0,0,0.3)]">
        <CardHeader>
          <CardTitle>
            <h1 className="font-serif text-3xl font-normal tracking-[-0.025em]">Iniciar sesión</h1>
          </CardTitle>
          <CardDescription>Accede al portal protegido de Claude AI Guard.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-5" onSubmit={submit}>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="login-username">Usuario</FieldLabel>
                <Input
                  id="login-username"
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  minLength={3}
                  maxLength={64}
                  required
                  autoFocus
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="login-password">Contraseña</FieldLabel>
                <Input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={8}
                  maxLength={128}
                  required
                />
              </Field>
            </FieldGroup>
            <Button className="w-full rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white" size="lg" type="submit" disabled={isSubmitting}>
              {isSubmitting && <Spinner data-icon="inline-start" />}
              {isSubmitting ? 'Verificando…' : 'Ingresar'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center text-sm text-muted-foreground">
          ¿Aún no tienes una cuenta?{' '}
          <Button asChild variant="link" className="px-1">
            <Link to="/register">Crear cuenta</Link>
          </Button>
        </CardFooter>
      </Card>
    </AuthShell>
  )
}
