import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

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
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/shared/interfaces/ui/field'
import { Input } from '@/shared/interfaces/ui/input'
import { Spinner } from '@/shared/interfaces/ui/spinner'
import { useAuth } from '@/contexts/iam/interfaces/auth-context'
import { AuthShell } from '@/contexts/iam/interfaces/auth-shell'
import { apiErrorMessage } from '@/shared/infrastructure/api/api-error'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const passwordMismatch = error === 'Las contraseñas no coinciden.'
  const weakPassword = error === 'La contraseña debe incluir al menos una letra y un número.'

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (password !== confirmation) {
      setError('Las contraseñas no coinciden.')
      return
    }
    if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setError('La contraseña debe incluir al menos una letra y un número.')
      return
    }
    setError(null)
    setIsSubmitting(true)
    try {
      await register(username, password)
      navigate('/', { replace: true })
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
            <h1 className="font-serif text-3xl font-normal tracking-[-0.025em]">Crear cuenta</h1>
          </CardTitle>
          <CardDescription>Registra un usuario local para acceder al portal.</CardDescription>
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
                <FieldLabel htmlFor="register-username">Usuario</FieldLabel>
                <Input
                  id="register-username"
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  pattern="[A-Za-z0-9._\-]+"
                  minLength={3}
                  maxLength={64}
                  required
                  autoFocus
                />
                <FieldDescription>
                  Usa letras, números, puntos, guiones o guiones bajos.
                </FieldDescription>
              </Field>
              <Field data-invalid={weakPassword}>
                <FieldLabel htmlFor="register-password">Contraseña</FieldLabel>
                <Input
                  id="register-password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={8}
                  maxLength={128}
                  required
                  aria-invalid={weakPassword}
                />
                <FieldDescription>
                  Mínimo 8 caracteres, con al menos una letra y un número.
                </FieldDescription>
              </Field>
              <Field data-invalid={passwordMismatch}>
                <FieldLabel htmlFor="register-confirmation">Confirmar contraseña</FieldLabel>
                <Input
                  id="register-confirmation"
                  type="password"
                  autoComplete="new-password"
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                  minLength={8}
                  maxLength={128}
                  required
                  aria-invalid={passwordMismatch}
                />
              </Field>
            </FieldGroup>
            <Button className="w-full rounded-xl bg-[#eceae3] text-[#222220] hover:bg-white" size="lg" type="submit" disabled={isSubmitting}>
              {isSubmitting && <Spinner data-icon="inline-start" />}
              {isSubmitting ? 'Creando cuenta…' : 'Crear cuenta'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center text-sm text-muted-foreground">
          ¿Ya tienes una cuenta?{' '}
          <Button asChild variant="link" className="px-1">
            <Link to="/login">Iniciar sesión</Link>
          </Button>
        </CardFooter>
      </Card>
    </AuthShell>
  )
}
